
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""This module contains the API Remote Control."""

import concurrent
from concurrent.futures import CancelledError, Future, TimeoutError
from dataclasses import dataclass
from enum import IntEnum, unique
from functools import partial
import os
from queue import Queue
from threading import Event, Lock, Thread
import time
from typing import Callable, Dict, List, Optional, Any

from .addon import PoliigonAddon
from .api import (
    ApiResponse,
    TIMEOUT,
    TIMEOUT_STREAM)
from .api_remote_control_params import (
    AddonRemoteControlParams,
    ApiJobParams,
    ApiJobParamsDownloadAsset,
    ApiJobParamsDownloadThumb,
    ApiJobParamsDownloadWMPreview,
    ApiJobParamsGetCategories,
    ApiJobParamsGetUserData,
    ApiJobParamsGetDownloadPrefs,
    ApiJobParamsGetAvailablePlans,
    ApiJobParamsGetUpgradePlan,
    ApiJobParamsPutUpgradePlan,
    ApiJobParamsResumePlan,
    ApiJobParamsGetAssets,
    ApiJobParamsLogin,
    ApiJobParamsPurchaseAsset,
    CmdLoginMode
)
from .assets import AssetData


@dataclass
class ApiResponseNewJob(ApiResponse):
    # This class is deliberately empty.
    # It only serves the purpose of being able to identify the ApiResponse
    # returned from get_new_job_response() via instanceof().
    pass


def get_new_job_response() -> ApiResponseNewJob:
    resp = ApiResponseNewJob(
        body={"data": []},
        ok=False,
        error="job waiting to execute"
    )
    return resp


@unique
class JobType(IntEnum):
    LOGIN = 0
    GET_USER_DATA = 1  # credits, subscription, user info
    GET_CATEGORIES = 2
    GET_DOWNLOAD_PREFS = 3
    GET_AVAILABLE_PLANS = 4
    GET_UPGRADE_PLAN = 5
    PUT_UPGRADE_PLAN = 6
    RESUME_PLAN = 7
    GET_ASSETS = 10
    DOWNLOAD_THUMB = 11
    PURCHASE_ASSET = 12
    DOWNLOAD_ASSET = 13
    DOWNLOAD_WM_PREVIEW = 14,
    UNIT_TEST = 15,
    EXIT = 99999


class ApiJob():
    """Describes an ApiJob and gets passed through the queues,
    subsequentyly being processed in thread_schedule and thread_collect.
    """

    def __init__(
        self,
        job_type: JobType,
        params: Optional[ApiJobParams] = None,
        callback_cancel: Optional[Callable] = None,
        callback_progress: Optional[Callable] = None,
        callback_done: Optional[Callable] = None,
        result: ApiResponse = None,
        future: Optional[Future] = None,
        timeout: Optional[float] = None
    ):
        self.job_type = job_type
        self.params = params
        self.callback_cancel = callback_cancel
        self.callback_progress = callback_progress
        self.callback_done = callback_done
        if result is not None:
            self.result = result
        else:
            self.result = get_new_job_response()
        self.future = future
        self.timeout = timeout

    def __eq__(self, other):
        return self.job_type == other.job_type and self.params == other.params

    def __str__(self) -> str:
        return f"{self.job_type.name}\n{str(self.params)}"


class ApiRemoteControl():

    def __init__(self, addon: PoliigonAddon):
        # Only members defined in addon_core.PoliigonAddon are allowed to be
        # used inside this module
        self._addon = addon
        self._addon_params = AddonRemoteControlParams()
        self._tm = addon._tm
        self._api = addon._api
        self._asset_index = addon._asset_index

        is_dev = addon._env.env_name != "prod"
        self.logger = self._addon.log_manager.initialize_logger(
            "APIRC", have_filehandler=is_dev)

        self.queue_jobs = Queue()
        self._start_thread_schedule()
        self.queue_jobs_done = Queue()
        self._start_thread_collect()

        self._start_thread_watchdog()

        self.lock_jobs_in_flight = Lock()
        self.jobs_in_flight = {}  # {job_type: [futures]}

        self.in_shutdown = False

        self.init_stats()

    def init_stats(self) -> None:
        """Initializes job statistics counters."""

        self.cnt_added = {}
        self.cnt_queued = {}
        self.cnt_cancelled = {}
        self.cnt_exec = {}
        self.cnt_done = {}
        self.cnt_restart_schedule = 0
        self.cnt_restart_collect = 0
        for job_type in JobType.__members__.values():
            self.cnt_added[job_type] = 0
            self.cnt_queued[job_type] = 0
            self.cnt_cancelled[job_type] = 0
            self.cnt_exec[job_type] = 0
            self.cnt_done[job_type] = 0

    def get_stats(self) -> Dict:
        """Returns job statistics counters as a dictionary."""

        stats = {}
        stats["Jobs added"] = self.cnt_added
        stats["Jobs queued"] = self.cnt_queued
        stats["Jobs cancelled"] = self.cnt_cancelled
        stats["Jobs exec"] = self.cnt_exec
        stats["Jobs done"] = self.cnt_done
        stats["Restart schedule"] = self.cnt_restart_schedule
        stats["Restart collect"] = self.cnt_restart_collect
        return stats

    def _start_thread_schedule(self) -> None:
        self.schedule_running = False
        thd_schedule_report_wrapped = self._tm.reporting_callable(
            self._thread_schedule.__name__,
            self._thread_schedule)
        self.thd_schedule = Thread(target=thd_schedule_report_wrapped)
        self.thd_schedule.name = "API RC Schedule"
        self.thd_schedule.start()

    def _start_thread_collect(self) -> None:
        self.collect_running = False
        thd_collect_report_wrapped = self._tm.reporting_callable(
            self._thread_collect.__name__,
            self._thread_collect)
        self.thd_collect = Thread(target=thd_collect_report_wrapped)
        self.thd_collect.name = "API RC Collect"
        self.thd_collect.start()

    def _start_thread_watchdog(self) -> None:
        self.watchdog_running = False
        self.event_watchdog = Event()
        thd_watchdog_report_wrapped = self._tm.reporting_callable(
            self._thread_watchdog.__name__,
            self._thread_watchdog)
        self.thd_watchdog = Thread(target=thd_watchdog_report_wrapped)
        self.thd_watchdog.name = "API RC Watchdog"
        self.thd_watchdog.start()

    def add_job_login(self,
                      mode: CmdLoginMode = CmdLoginMode.LOGIN_BROWSER,
                      email: Optional[str] = None,
                      pwd: Optional[str] = None,
                      time_since_enable: Optional[int] = None,
                      callback_cancel: Optional[Callable] = None,
                      callback_progress: Optional[Callable] = None,
                      callback_done: Optional[Callable] = None,
                      force: bool = True
                      ) -> None:
        """Convenience function to add a login or logout job."""

        if mode == CmdLoginMode.LOGOUT:
            self.empty_pipeline()
        else:  # login
            self._asset_index.flush()

        params = ApiJobParamsLogin(mode, email, pwd, time_since_enable)
        self.add_job(
            job_type=JobType.LOGIN,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            force=force,
            timeout=TIMEOUT)

    def add_job_get_user_data(self,
                              user_name: str,
                              user_id: str,
                              callback_cancel: Optional[Callable] = None,
                              callback_progress: Optional[Callable] = None,
                              callback_done: Optional[Callable] = None,
                              force: bool = True
                              ) -> None:
        """Convenience function to add a get user data job."""

        params = ApiJobParamsGetUserData(user_name, user_id)
        self.add_job(
            job_type=JobType.GET_USER_DATA,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            force=force,
            timeout=TIMEOUT)

    def add_job_get_download_prefs(self,
                                   *,
                                   callback_cancel: Optional[Callable] = None,
                                   callback_progress: Optional[Callable] = None,
                                   callback_done: Optional[Callable] = None,
                                   force: bool = True
                                   ) -> None:
        """Convenience function to get user download preferences."""

        params = ApiJobParamsGetDownloadPrefs()
        self.add_job(
            job_type=JobType.GET_DOWNLOAD_PREFS,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            force=force,
            timeout=TIMEOUT)

    def add_job_get_available_plans(self,
                                    callback_cancel: Optional[Callable] = None,
                                    callback_progress: Optional[Callable] = None,
                                    callback_done: Optional[Callable] = None,
                                    force: bool = True
                                    ) -> None:
        params = ApiJobParamsGetAvailablePlans()
        self.add_job(
            job_type=JobType.GET_AVAILABLE_PLANS,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            force=force,
            timeout=TIMEOUT)

    def add_job_get_upgrade_plan(self,
                                 callback_cancel: Optional[Callable] = None,
                                 callback_progress: Optional[Callable] = None,
                                 callback_done: Optional[Callable] = None,
                                 force: bool = True
                                 ) -> None:
        params = ApiJobParamsGetUpgradePlan()
        self.add_job(
            job_type=JobType.GET_UPGRADE_PLAN,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            force=force,
            timeout=TIMEOUT)

    def add_job_put_upgrade_plan(self,
                                 callback_cancel: Optional[Callable] = None,
                                 callback_progress: Optional[Callable] = None,
                                 callback_done: Optional[Callable] = None,
                                 force: bool = True
                                 ) -> None:
        params = ApiJobParamsPutUpgradePlan()
        self.add_job(
            job_type=JobType.PUT_UPGRADE_PLAN,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            force=force,
            timeout=TIMEOUT)

    def add_job_resume_plan(self,
                            callback_cancel: Optional[Callable] = None,
                            callback_progress: Optional[Callable] = None,
                            callback_done: Optional[Callable] = None,
                            force: bool = True
                            ) -> None:
        params = ApiJobParamsResumePlan()
        self.add_job(
            job_type=JobType.RESUME_PLAN,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            force=force,
            timeout=TIMEOUT)

    def add_job_get_categories(self,
                               callback_cancel: Optional[Callable] = None,
                               callback_progress: Optional[Callable] = None,
                               callback_done: Optional[Callable] = None,
                               force: bool = True
                               ) -> None:
        """Convenience function to add a get categories job."""

        params = ApiJobParamsGetCategories()
        self.add_job(
            job_type=JobType.GET_CATEGORIES,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            force=force,
            timeout=TIMEOUT)

    def add_job_get_assets(self,
                           library_paths: List[str],
                           tab: str,  # KEY_TAB_ONLINE, KEY_TAB_MY_ASSETS
                           category_list: List[str] = ["All Assets"],
                           search: str = "",
                           idx_page: int = 1,
                           page_size: int = 10,
                           force_request: bool = False,
                           do_get_all: bool = True,
                           callback_cancel: Optional[Callable] = None,
                           callback_progress: Optional[Callable] = None,
                           callback_done: Optional[Callable] = None,
                           force: bool = True,
                           ignore_old_names: bool = True
                           ) -> None:
        """Convenience function to add a get assets job."""

        params = ApiJobParamsGetAssets(library_paths,
                                       tab,
                                       category_list,
                                       search,
                                       idx_page,
                                       page_size,
                                       force_request,
                                       do_get_all,
                                       ignore_old_names)
        self.add_job(
            job_type=JobType.GET_ASSETS,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            force=force,
            timeout=TIMEOUT)

    def add_job_download_thumb(self,
                               asset_id: int,
                               url: str,
                               path: str,
                               idx_thumb: int = -1,
                               do_update: bool = False,
                               callback_cancel: Optional[Callable] = None,
                               callback_progress: Optional[Callable] = None,
                               callback_done: Optional[Callable] = None,
                               force: bool = False
                               ) -> None:
        """Convenience function to add a download thumb job."""

        params = ApiJobParamsDownloadThumb(
            asset_id, url, path, do_update, idx_thumb=idx_thumb)
        temp_path = f"{path}_temp"
        if not os.path.isfile(temp_path):
            fwriter = open(temp_path, "wb")
            fwriter.close()
        elif os.path.isfile(path):
            job = ApiJob(
                job_type=JobType.DOWNLOAD_THUMB,
                params=params,
                callback_cancel=callback_cancel,
                callback_progress=callback_progress,
                callback_done=callback_done)
            callback_done(job=job)
            return
        else:
            return

        self.add_job(
            job_type=JobType.DOWNLOAD_THUMB,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            force=force,
            timeout=TIMEOUT_STREAM)

    def add_job_purchase_asset(
        self,
        asset_data: AssetData,
        category_list: List[str] = ["All Assets"],
        search: str = "",
        job_download: Optional[Callable] = None,  # type: ApiJob
        callback_cancel: Optional[Callable] = None,
        callback_progress: Optional[Callable] = None,
        callback_done: Optional[Callable] = None,
        force: bool = True
    ) -> None:
        """Convenience function to add a purchase asset job."""

        params = ApiJobParamsPurchaseAsset(asset_data,
                                           category_list,
                                           search,
                                           job_download)
        self.add_job(
            job_type=JobType.PURCHASE_ASSET,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            force=force,
            timeout=TIMEOUT)

    def create_job_download_asset(self,
                                  asset_data: AssetData,
                                  size: str = "2K",
                                  size_bg: str = "",
                                  type_bg: str = "EXR",
                                  lod: str = "NONE",
                                  variant: str = "",
                                  download_lods: bool = False,
                                  native_mesh: bool = True,
                                  renderer: str = "",
                                  callback_cancel: Optional[Callable] = None,
                                  callback_progress: Optional[Callable] = None,
                                  callback_done: Optional[Callable] = None
                                  ) -> ApiJob:
        """Convenience function to add a download asset job."""

        params = ApiJobParamsDownloadAsset(
            self._addon, asset_data, size, size_bg, type_bg, lod, variant,
            download_lods, native_mesh, renderer)
        job = ApiJob(
            job_type=JobType.DOWNLOAD_ASSET,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            timeout=TIMEOUT_STREAM
        )

        # Due to the limitation of the number of threads, the download thread
        # may not start immediately. In that case it would seem, as if nothing
        # is happening.
        asset_data.state.dl.start()
        if callback_progress is not None:
            callback_progress(job)

        return job

    def add_job_download_asset(self,
                               asset_data: AssetData,
                               size: str = "2K",
                               size_bg: str = "",
                               type_bg: str = "EXR",
                               lod: str = "NONE",
                               variant: str = "",
                               download_lods: bool = False,
                               native_mesh: bool = True,
                               renderer: str = "",
                               callback_cancel: Optional[Callable] = None,
                               callback_progress: Optional[Callable] = None,
                               callback_done: Optional[Callable] = None,
                               force: bool = True
                               ) -> None:
        """Convenience function to add a download asset job."""

        self.cnt_added[JobType.DOWNLOAD_ASSET] += 1
        job = self.create_job_download_asset(
            asset_data,
            size,
            size_bg,
            type_bg,
            lod,
            variant,
            download_lods,
            native_mesh,
            renderer,
            callback_cancel,
            callback_progress,
            callback_done
        )
        self.enqueue_job(job, force)

    def add_job_download_wm_preview(
        self,
        asset_data: AssetData,
        renderer: str = "",
        callback_cancel: Optional[Callable] = None,
        callback_progress: Optional[Callable] = None,
        callback_done: Optional[Callable] = None,
        force: bool = True
    ) -> None:
        """Convenience function to add a download WM preview job."""

        params = ApiJobParamsDownloadWMPreview(asset_data,
                                               renderer)
        self.add_job(
            job_type=JobType.DOWNLOAD_WM_PREVIEW,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            force=force,
            timeout=TIMEOUT_STREAM)

    def add_job_exit(self) -> None:
        """Convenience function to add an APIRC exit job."""

        job = ApiJob(
            job_type=JobType.EXIT,
            params={},
            callback_cancel=None,
            callback_progress=None,
            callback_done=None)
        # Enqueue directly, as actual enqueue_jobs() gets disabled before
        # shutdown
        self.queue_jobs.put(job)

    def _is_job_already_enqueued(self, job: ApiJob) -> bool:
        """Returns True, if an identical job exists already."""

        with self.lock_jobs_in_flight:
            jobs_in_flight_copy = self.jobs_in_flight.copy()

        try:
            return job in jobs_in_flight_copy[job.job_type]
        except KeyError:
            return False

    def enqueue_job(self, job: ApiJob, force: bool = True) -> None:
        """Enqueúes a single ApiJob.

        Arguments:
        force: Default True, False: Enqueue only, if not queued already
        """

        if not force and self._is_job_already_enqueued(job):
            return

        self.cnt_queued[job.job_type] += 1
        self.queue_jobs.put(job)

    def add_job(self,
                job_type: JobType,
                params: Any = {},  # Class from API RC Params
                callback_cancel: Optional[Callable] = None,
                callback_progress: Optional[Callable] = None,
                callback_done: Optional[Callable] = None,
                force: bool = True,
                timeout: Optional[float] = None
                ) -> None:
        """Adds a job to be processed by API remote control."""

        self.cnt_added[job_type] += 1

        job = ApiJob(
            job_type=job_type,
            params=params,
            callback_cancel=callback_cancel,
            callback_progress=callback_progress,
            callback_done=callback_done,
            timeout=timeout)
        self.enqueue_job(job, force)

    def _release_job(self, job: ApiJob) -> None:
        """Removes a finished job from 'in flight' list."""

        try:
            with self.lock_jobs_in_flight:
                self.jobs_in_flight[job.job_type].remove(job)
        except (KeyError, ValueError):
            pass  # List of job type not found or job not found in list

    def enqueue_job_shutdown(self, job: ApiJob, force: bool = True):
        """Used to replace enqueue_job() method during shutdown to avoid any
        new jobs being enqueued.

        Function is deliberately empty!
        """
        pass

    def empty_pipeline(self) -> None:
        """Gets rid of any jobs in API RC's pipeline.

        In what way is this different to wait_for_all()?
        wait_for_all() will get rid of all (or just a single type) jobs
        currently in the pipeline. But it does make no attempt to avoid new
        jobs being added. For example getting user data spawns five different
        follow up jobs, some of those then spawning more follow up jobs (e.g.
        the get asstes ones). empty_pipeline()
        """

        # Have all jobs already in thread pool exit as early as possible
        self.in_shutdown = True

        # Prevent any new jobs from being queued
        f_enqueue_job_bak = self.enqueue_job
        self.enqueue_job = self.enqueue_job_shutdown
        # Empty job queue to prevent new jobs from being scheduled in
        # thread pool
        while not self.queue_jobs.empty():
            self.queue_jobs.get_nowait()

        # Schedule point to allow threads to run home
        # Sleep should be short, but longer than OS's tick
        time.sleep(0.050)  # 50 ms

        self.wait_for_all(timeout=None)

        # Re-enable normal operation
        self.enqueue_job = f_enqueue_job_bak
        self.in_shutdown = False

    def shutdown(self) -> None:
        """Stops remote control's threads."""

        # Tear watchdog down, first (we do not want it to restart anything)
        self.watchdog_running = False
        self.event_watchdog.set()
        self.thd_watchdog.join()
        # Have all jobs already in thread pool exit as early as possible
        self.in_shutdown = True
        # Prevent any new jobs from being queued
        self.enqueue_job = self.enqueue_job_shutdown
        # Empty job queue to prevent new jobs from being scheduled in
        # thread pool
        while not self.queue_jobs.empty():
            self.queue_jobs.get_nowait()
        # Enqueue the "exit job", which will lead to _thread_schedule and
        # _thread_collect to exit
        self.add_job_exit()
        # Lastly wait for eveything to come to halt.
        # timeout=None, use job type specific timeouts
        self.wait_for_all(timeout=None)

    def _wait_for_type(self,
                       jobs_in_flight_copy: Dict,
                       job_type: JobType,
                       do_wait: bool,
                       timeout: Optional[int]
                       ) -> None:
        """Cancels all jobs of given type, optionally waits until cancelled."""

        for job in jobs_in_flight_copy[job_type]:
            try:
                with self.lock_jobs_in_flight:
                    self.jobs_in_flight[job.job_type].remove(job)
            except (KeyError, AttributeError):
                pass

            if job.result is None:
                job.result = ApiResponse(ok=True,
                                         body={"data": []},
                                         error="job cancelled")

            if job.future is None:
                self.logger.warning(f"Future is None: {job.job_type.name}")
                continue
            elif job.future.cancel():
                self.cnt_cancelled[job.job_type] += 1
                continue
            try:
                job.callback_cancel()
            except TypeError:
                pass  # Not every job has a cancel callback
            if do_wait:
                try:
                    if timeout is None:
                        timeout = job.timeout
                    job.future.result(timeout)
                except (CancelledError,
                        TimeoutError,
                        concurrent.futures._base.TimeoutError) as e:
                    msg = ("API RC's job did not return upon cancel. "
                           f"Timeout: {timeout}\nJob: {str(job)}")
                    self.logger.exception(msg)
                    self._addon._api.report_exception(e)

    def wait_for_all(self,
                     job_type: Optional[JobType] = None,
                     do_wait: bool = True,
                     timeout: Optional[int] = None
                     ) -> None:
        """Cancels all jobs or just a given type, optionally waits until
        cancelled.

        Arguments:
        job_type: Specify to cancel jobs of a certain type, None for all types
        do_wait: Set to True to wait for cancellation, otherwise just cancel
                 and return immediately.
        timeout: Time to wait for futures to finish. If None,
                 job type specific timeouts will be used (defined in
                 add_job_xyz() functions below).
        """

        with self.lock_jobs_in_flight:
            jobs_in_flight_copy = self.jobs_in_flight.copy()

        if job_type is None:
            for job_type in jobs_in_flight_copy:
                self._wait_for_type(
                    jobs_in_flight_copy, job_type, do_wait, timeout)
        elif job_type in jobs_in_flight_copy:
            self._wait_for_type(
                jobs_in_flight_copy, job_type, do_wait, timeout)

    def is_job_type_active(self, job_type: JobType) -> bool:
        """Returns True if there's at least one job of given type in flight."""

        return len(self.jobs_in_flight.get(job_type, [])) > 0

    def _thread_schedule(self) -> None:
        """Thread waiting on job queue to start jobs in thread pool."""

        self.schedule_running = True
        while self.schedule_running:
            job = self.queue_jobs.get()

            self.cnt_exec[job.job_type] += 1

            if job.job_type != JobType.EXIT:
                with self.lock_jobs_in_flight:
                    try:
                        self.jobs_in_flight[job.job_type].append(job)
                    except KeyError:
                        self.jobs_in_flight[job.job_type] = [job]

            if job.job_type != JobType.EXIT:
                job.future = self._tm.queue_thread(
                    job.params.thread_execute,
                    job.params.POOL_KEY,
                    max_threads=None,
                    foreground=False,
                    api_rc=self,
                    job=job
                )
            else:
                # JobType.EXIT
                self.queue_jobs_done.put(job)  # stop collector
                self.schedule_running = False

            def callback_enqueue_done(fut, job: ApiJob) -> None:
                self.queue_jobs_done.put(job)

            cb_done = partial(callback_enqueue_done, job=job)
            try:
                job.future.add_done_callback(cb_done)
            except AttributeError as e:
                # JobType.EXIT has no Future
                if job.job_type != JobType.EXIT:
                    msg = f"Job {job.job_type.name} has no Future"
                    self.logger.exception(msg)
                    self._addon._api.report_exception(e)

    def _thread_collect(self) -> None:
        """Thread awaiting threaded jobs to finish, then executes job's post
        processing.
        """

        self.collect_running = True
        while self.collect_running:
            job = self.queue_jobs_done.get()

            if job.job_type != JobType.EXIT:
                try:
                    job.params.finish(self, job)
                except BaseException as e:
                    # Finish handlers are not allowed to tear down our
                    # collect thread...
                    msg = ("A job's finish function failed unexpectedly: "
                           f"{str(job)}")
                    self.logger.exception(msg)
                    self._addon._api.report_exception(e)
            else:
                # JobType.EXIT
                self.collect_running = False
                break

            try:
                job.callback_done(job=job)
            except TypeError:
                pass  # There is no done callback
            except BaseException as e:
                # Done callbacksare not allowed to tear down our
                # collect thread...
                msg = ("A job's done callback failed unexpectedly: "
                       f"{str(job)}")
                self.logger.exception(msg)
                self._addon._api.report_exception(e)

            self._release_job(job)
            self.cnt_done[job.job_type] += 1

    def _thread_watchdog(self) -> None:
        self.watchdog_running = True
        while self.watchdog_running:
            # Event used as a sleep (will only get set during shutdown)
            self.event_watchdog.wait(1.0)

            if not self.watchdog_running:
                break

            if not self.thd_schedule.is_alive():
                self.cnt_restart_schedule += 1
                self._start_thread_schedule()

                msg = f"API RC's schedule failed ({self.cnt_restart_schedule})"
                self._addon._api.report_message(
                    "apirc_thread_failure_schedule", msg, "error")
                self.logger.critical(msg)

            if not self.thd_collect.is_alive():
                self.cnt_restart_collect += 1
                self._start_thread_collect()

                msg = f"API RC's collect failed ({self.cnt_restart_collect})"
                self._addon._api.report_message(
                    "apirc_thread_failure_collect", msg, "error")
                self.logger.critical(msg)
