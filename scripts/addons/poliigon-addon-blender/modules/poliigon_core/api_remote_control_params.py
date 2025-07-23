
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

"""This module contains the API Remote Control parameter classes."""

from dataclasses import dataclass, field
from enum import IntEnum, unique
from functools import partial
import os
from typing import Callable, Dict, List, Optional

from .user import (PoliigonSubscription,
                   PoliigonUser,
                   UserDownloadPreferences)
from .plan_manager import (PoliigonPlanUpgradeInfo,
                           PlanUpgradeStatus,
                           SubscriptionState)
from .download_asset import AssetDownload
from .api import ApiResponse, ERR_NOT_ENOUGH_CREDITS
from .assets import AssetData
from .thread_manager import PoolKeys


@unique
class CmdLoginMode(IntEnum):
    # Do not have zero value members!
    LOGIN_CREDENTIALS = 1
    LOGIN_BROWSER = 2
    LOGOUT = 3
    LOGIN_CANCEL = 4


# For use in query keys
KEY_TAB_IMPORTED = "imported"
KEY_TAB_MY_ASSETS = "my_assets"
KEY_TAB_ONLINE = "poliigon"

CATEGORY_ALL = "All Assets"
CATEGORY_FREE = "Free"  # this is a virtual category

# CATEGORY_MAPPING_ dicts are used to translate category names between
# API convention (as received/sent from/to API) to local/plugin convention
# (as for example used in AssetIndex, see for example
# CATEGORY_NAME_TO_ASSET_TYPE in assets.py).
CATEGORY_MAPPING_API_TO_LOCAL = {
    # Key API convention: Local/plugin convention
    "HDRs": "HDRIs"
}
CATEGORY_MAPPING_LOCAL_TO_API = {
    # Key Local/plugin convention: API convention
    "HDRIs": "HDRs"
}


IDX_PAGE_ACCUMULATED = -1
PAGE_SIZE_ACCUMULATED = 1000000


def get_search_key(tab: str, search: str, category_list: List[str]) -> str:
    """Returns a search/query string."""

    if search != "":
        sep = "@"
        search_ext = f"{sep}{search}"
    else:
        sep = "/"
        search_ext = ""
    categories = sep.join(category_list)
    key = f"{tab}{sep}{categories}{search_ext}"
    return key


@dataclass
class ApiResponseShutdown(ApiResponse):
    # This class is deliberately empty.
    # It only serves the purpose of being able to identify the ApiResponse
    # returned from get_shutdown_response() via instanceof().
    pass


def get_shutdown_response() -> ApiResponseShutdown:
    resp = ApiResponseShutdown(
        body={"data": []},
        # We don't want any error reporting, due to us shutting down
        ok=True,
        error="job shutdown"
    )
    return resp


# TODO(Andreas): Move these THUMB_SIZE_ constants to a better place.
# NOTE: THUMB_SIZE_DOWNLOAD needs to match one of the available download sizes!
THUMB_SIZE_MIN = 100
THUMB_SIZE_PROG = 145  # progress bar switches to short label
THUMB_SIZE_DEFAULT = 150
THUMB_SIZE_MAX = 200
THUMB_SIZE_DOWNLOAD = 300


@dataclass
class AddonRemoteControlParams():
    """ Parameters to be set in the Addon Side.

    NOTE: These processes are ran by default by API RC, so it is not possible
    to only parse using done_callback parameter in the ApiJob"""

    online_assets_chunk_size: int = 100
    my_assets_chunk_size: int = 100
    callback_get_categories_done: Optional[Callable] = None
    callback_get_asset_done: Optional[Callable] = None
    callback_get_user_data_done: Optional[Callable] = None
    callback_get_download_prefs_done: Optional[Callable] = None
    callback_get_available_plans: Optional[Callable] = None
    callback_get_upgrade_plan: Optional[Callable] = None
    callback_put_upgrade_plan: Optional[Callable] = None
    callback_resume_plan: Optional[Callable] = None


@dataclass
class ApiJobParams():
    """Job parameters.

    NOTE: Nothing in here.
          Only used as a parent class for type hints and defining interfaces.
    """

    def __eq__(self, other):
        raise NotImplementedError(
            "Some derived class forgot to implement __eq__")

    def __str__(self) -> str:
        raise NotImplementedError(
            "Some derived class forgot to implement __str__")

    def thread_execute(self,
                       api_rc,  # : ApiRemoteControl
                       job  # : ApiJob
                       ) -> None:
        """Executes job in a thread, started from thread_schedule."""

        raise NotImplementedError

    def finish(self,
               api_rc,  # : ApiRemoteControl
               job  # : ApiJob
               ) -> None:
        """Finishes a job, called from thread_collect."""

        raise NotImplementedError


@dataclass
class ApiJobParamsLogin(ApiJobParams):
    """Login specific parameters"""

    mode: CmdLoginMode
    email: Optional[str] = None
    pwd: Optional[str] = None
    time_since_enable: Optional[int] = None

    POOL_KEY = PoolKeys.INTERACTIVE

    def __eq__(self, other):
        return self.mode == other.mode and self.email == other.email

    def __str__(self) -> str:
        # No email or password, as the resulting string might be reported to
        # server!
        return (
            f"ApiJobParamsLogin - mode: {self.mode.name}, "
            f"time_since_enable: {self.time_since_enable}"
        )

    def _exec_job_login_credential(self, api_rc, job) -> None:
        """Executes a login with email and password.
        Gets called in thread (thread_exec_job_login).
        """

        job.result = api_rc._api.log_in(self.email,
                                        self.pwd,
                                        self.time_since_enable)

    def _exec_job_login_browser(self, api_rc, job) -> None:
        """Executes a login via browser.
        Gets called in thread (thread_exec_job_login).
        """

        job.result = api_rc._api.log_in_with_website(
            self.time_since_enable)
        if job.callback_cancel is not None and job.callback_cancel():
            return

        job.result = api_rc._api.poll_login_with_website_success(
            timeout=300,
            cancel_callback=job.callback_cancel,
            time_since_enable=self.time_since_enable
        )

    def _exec_job_logout(self, api_rc, job) -> None:
        """Executes a logout.
        Gets called in thread (thread_exec_job_login).
        """

        job.result = api_rc._api.log_out()

    def thread_execute(self, api_rc, job) -> None:
        """Executes any login/logout jobs in a thread,
        started from thread_schedule.
        """

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return

        if self.mode == CmdLoginMode.LOGIN_CREDENTIALS:
            self._exec_job_login_credential(api_rc, job)
        elif self.mode == CmdLoginMode.LOGIN_BROWSER:
            self._exec_job_login_browser(api_rc, job)
        elif self.mode == CmdLoginMode.LOGOUT:
            self._exec_job_logout(api_rc, job)

    def finish(self, api_rc, job) -> None:
        """Finishes login/logout jobs, called from thread_collect."""

        if api_rc.in_shutdown:
            return

        # TODO(Andreas): Evaluate res and store in prefs?
        #                Currently done in CommandDataLogin.callback_xyz_done.
        #                Not sure, yet, where the better place would be.
        #                To have it here, would need abstract ways to set prefs.

        # TODO(Andreas): Strange! Should likely be fixed in addon-core.api
        #                or even server side. Will look into it at a later point.
        if "results" in job.result.body:
            # Login via browser response
            job.result.body = job.result.body["results"]

        if not job.result.ok or self.mode == CmdLoginMode.LOGOUT:
            api_rc.logger.debug("### Set user None")
            api_rc._addon.user = None
        else:
            user_info = job.result.body["user"]

            # Checking if student or teacher - the value can be set as null in
            # the user_data, due to that we are falling back to an empty string
            user_use = user_info.get("how_will_you_use_poliigon", "")
            user_use = user_use if user_use is not None else ""
            is_student = "student" in user_use
            is_teacher = "teacher" in user_use

            subscription_info = job.result.body.get("subscription", {})
            plan = PoliigonSubscription()
            plan.update_from_dict(subscription_info)
            api_rc._addon.user = PoliigonUser(
                user_name=user_info["name"],
                user_id=user_info["id"],
                is_student=is_student,
                is_teacher=is_teacher,
                plan=plan
            )
            api_rc._addon.upgrade_manager.refresh(clean_plans=True)


@dataclass
class ApiJobParamsGetCategories(ApiJobParams):
    """Get Categories specific parameters"""

    # no parameters needed
    POOL_KEY = PoolKeys.INTERACTIVE

    def __eq__(self, other):
        return True

    def __str__(self) -> str:
        # Assuming user ID is fine in here, as we know it anyway!
        return "ApiJobParamsGetCategories"

    def thread_execute(self, api_rc, job) -> None:
        """Executes any get categories jobs in a thread,
        started from thread_schedule.
        """

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return

        job.result = api_rc._api.categories()

    def finish(self, api_rc, job) -> None:
        """Finishes get categories jobs, called from thread_collect."""

        # For the moment nothing to do here.
        # Will likely chanage with dynamic category counts.
        pass


@dataclass
class ApiJobParamsGetUserData(ApiJobParams):
    """Get User Data specific parameters"""

    user_name: str
    user_id: str

    POOL_KEY = PoolKeys.INTERACTIVE

    def __eq__(self, other):
        return self.user_name == other.user_name and \
            self.user_id == other.user_id

    def __str__(self) -> str:
        # Assuming user ID is fine in here, as we know it anyway!
        return f"ApiJobParamsGetUserData - user id: {self.user_id}"

    def _get_user_info_from_api(self, api_rc) -> bool:
        """Fetches the user information.
        Gets called in thread (thread_exec_job_get_user_data).
        """

        req = api_rc._addon._api.get_user_info()
        if req.ok:
            user_data = req.body.get("user", {})
            api_rc._addon.user.user_name = user_data.get("name", None)
            api_rc._addon.user.user_id = user_data.get("id", None)

            # Checking if student or teacher - the value can be set as null in
            # the user_data, due to that we are falling back to an empty string
            user_use = user_data.get("how_will_you_use_poliigon", "")
            user_use = user_use if user_use is not None else ""
            is_student = "student" in user_use
            is_teacher = "teacher" in user_use

            api_rc._addon.user.is_student = is_student
            api_rc._addon.user.is_teacher = is_teacher
            api_rc._addon.login_error = None
        else:
            api_rc._addon.login_error = req.error
            api_rc.logger.error(req.error)

    def thread_execute(self, api_rc, job) -> None:
        """Executes any get user data jobs in a thread,
        started from thread_schedule.
        """

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return

        if api_rc._addon.user is None:
            api_rc._addon.user = PoliigonUser(
                user_name=self.user_name,
                user_id=self.user_id,
                plan=PoliigonSubscription(
                    subscription_state=SubscriptionState.NOT_POPULATED))

        self._get_user_info_from_api(api_rc)
        if api_rc._addon.login_error is not None:
            api_rc.logger.error(
                f"get_user_info failed: {api_rc._addon.login_error}")
        else:
            try:
                api_rc._addon._get_credits()
                api_rc._addon._get_subscription_details()
            except Exception as e:
                # TODO(Andreas): Had an issue in the beginning, by now
                #                it should be fixed and exception no longer
                #                be an issue. Remove try/except
                api_rc.logger.error(f"### exc: _get_credits...\n{e}")

        api_rc._addon.upgrade_manager.refresh()

        # TODO(Andreas): maybe more checks needed?
        ok = api_rc._addon.user is not None
        ok &= api_rc._addon.login_error is None
        job.result = ApiResponse(ok=ok,
                                 body={},
                                 error="")

    def finish(self, api_rc, job) -> None:
        """Finishes get user data jobs, called from thread_collect."""

        if api_rc.in_shutdown:
            return

        if not job.result.ok:
            return

        addon_params = api_rc._addon_params

        api_rc.add_job_get_available_plans(
            callback_cancel=None,
            callback_progress=None,
            callback_done=addon_params.callback_get_available_plans,
            force=True
        )

        api_rc.add_job_get_download_prefs(
            callback_cancel=None,
            callback_progress=None,
            callback_done=addon_params.callback_get_download_prefs_done,
            force=True)

        # TODO(Andreas): Maybe have an option to select follow up jobs.
        #                See: https://github.com/poliigon/poliigon-addon-core/pull/188#discussion_r1346322792
        api_rc.add_job_get_categories(
            callback_cancel=None,
            callback_progress=None,
            callback_done=addon_params.callback_get_categories_done,
            force=True

        )
        api_rc.add_job_get_assets(
            library_paths=api_rc._addon.get_library_paths(),
            tab=KEY_TAB_ONLINE,
            category_list=[CATEGORY_ALL],
            search="",
            idx_page=1,
            page_size=addon_params.online_assets_chunk_size,
            force_request=False,
            do_get_all=True,
            callback_cancel=None,
            callback_progress=None,
            callback_done=addon_params.callback_get_asset_done,
            force=True
        )
        api_rc.add_job_get_assets(
            library_paths=api_rc._addon.get_library_paths(),
            tab=KEY_TAB_MY_ASSETS,
            category_list=[CATEGORY_ALL],
            search="",
            idx_page=1,
            page_size=addon_params.my_assets_chunk_size,
            force_request=True,
            do_get_all=True,
            callback_cancel=None,
            callback_progress=None,
            callback_done=addon_params.callback_get_asset_done,
            force=True
        )


@dataclass
class ApiJobParamsGetDownloadPrefs(ApiJobParams):
    """Get User Download Preferences."""

    POOL_KEY = PoolKeys.INTERACTIVE

    def __eq__(self, other):
        return True

    def __str__(self) -> str:
        return "ApiJobParamsGetDownloadPrefs"

    @staticmethod
    def _fetch_user_maps_preferences(api_rc) -> ApiResponse:
        res = api_rc._addon._api.get_download_preferences()
        return res

    def thread_execute(self, api_rc, job) -> None:
        """Executes the request for getting Download Preferences."""

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return

        if api_rc._addon.user is None:
            api_rc.logger.error(
                "User not defined when fetching Download preferences.")
            return

        job.result = self._fetch_user_maps_preferences(api_rc)
        if not job.result.ok:
            api_rc.logger.error(
                f"Error fetching download preferences. {job.result.error}")

    def finish(self, api_rc, job) -> None:
        """Finishes get Download Prefs, and stores in Poliigon User."""

        if api_rc.in_shutdown:
            return

        if not job.result.ok or job.result.body.get("results") is None:
            return

        map_preferences = job.result.body.get("results")
        api_rc._addon.user.map_preferences = UserDownloadPreferences(
            map_preferences)


@dataclass
class ApiJobParamsGetAvailablePlans(ApiJobParams):
    """Get User Upgrade Plans."""

    POOL_KEY = PoolKeys.INTERACTIVE

    def __eq__(self, other):
        return True

    def __str__(self) -> str:
        return "ApiJobParamsGetAvailablePlans"

    def thread_execute(self, api_rc, job) -> None:
        """Executes the request for getting User's Upgrade Plans."""

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return

        if api_rc._addon.user is None:
            api_rc.logger.error(
                "User not defined when fetching Available Plans.")
            return

        if api_rc._addon.is_free_user():
            job.ok = True
            job.result = ApiResponse(ok=True,
                                     body={"data": []},
                                     error=("Fetching available plans for "
                                            "free user cancelled."))
            return

        job.result = api_rc._addon._api.get_user_available_plans()
        if not job.result.ok:
            api_rc.logger.error(
                f"Error fetching upgrade Plans. {job.result.error}")

    def finish(self, api_rc, job) -> None:
        """Finishes get Upgrade Plans, and stores in Poliigon User
        Upgrade Manager.
        """

        if api_rc.in_shutdown:
            return

        if not job.result.ok or job.result.body.get("results") is None:
            api_rc._addon.upgrade_manager.refresh()
            return

        results = job.result.body.get("results", {})
        api_rc._addon.upgrade_manager.refresh(results)

        if api_rc._addon.upgrade_manager.upgrade_plan is not None:
            api_rc.add_job_get_upgrade_plan(
                callback_done=api_rc._addon_params.callback_get_upgrade_plan)


@dataclass
class ApiJobParamsGetUpgradePlan(ApiJobParams):
    """Get Information for Upgrading current Plan."""

    POOL_KEY = PoolKeys.INTERACTIVE

    def __eq__(self, other):
        return True

    def __str__(self) -> str:
        return "ApiJobParamsGetUpgradePlan"

    def thread_execute(self, api_rc, job) -> None:
        """Executes the request for getting Information for Upgrading current
        Plan.
        """

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return

        if api_rc._addon.user is None:
            api_rc.logger.error(
                "User not defined when getting Upgrade Plan info.")
            return
        upgrade_manager = api_rc._addon.upgrade_manager
        if upgrade_manager.upgrade_plan is None:
            api_rc.logger.error(
                "Upgrade plan not defined when getting Upgrade Plan info.")
            return

        to_upgrade_plan_id = upgrade_manager.upgrade_plan.plan_price_id
        job.result = api_rc._addon._api.get_upgrade_plan(to_upgrade_plan_id)

        if not job.result.ok:
            api_rc.logger.error(
                f"Error getting Upgrading Plan. {job.result.error}")

    def finish(self, api_rc, job) -> None:
        """Finishes get Upgrade Plan, and stores Upgrade information."""

        if api_rc.in_shutdown:
            return

        if not job.result.ok or job.result.body.get("results") is None:
            if api_rc._addon.user is not None:
                info = PoliigonPlanUpgradeInfo(
                    ok=False, error=job.result.error)
                api_rc._addon.upgrade_manager.upgrade_info = info
            return

        info = PoliigonPlanUpgradeInfo.from_dict(
            job.result.body.get("results"))
        api_rc._addon.upgrade_manager.upgrade_info = info
        api_rc._addon.upgrade_manager.refresh()


@dataclass
class ApiJobParamsPutUpgradePlan(ApiJobParams):
    """Confirm current Plan Upgrade."""

    POOL_KEY = PoolKeys.INTERACTIVE

    def __eq__(self, other):
        return True

    def __str__(self) -> str:
        return "ApiJobParamsPutUpgradePlan"

    def thread_execute(self, api_rc, job) -> None:
        """Executes the request for confirming the Upgrade of the current
        Plan.
        """

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return
        if api_rc._addon.user is None:
            api_rc.logger.error(
                "User not defined when confirming Upgrade Plan.")
            return
        if api_rc._addon.upgrade_manager.upgrade_plan is None:
            api_rc.logger.error(
                "Upgrade plan not defined when confirming Upgrade Plan.")
            return

        to_upgrade_plan_id = api_rc._addon.upgrade_manager.upgrade_plan.plan_price_id
        job.result = api_rc._addon._api.put_upgrade_plan(to_upgrade_plan_id)

        if not job.result.ok:
            api_rc.logger.error(
                f"Error confirming Plan Upgrade. {job.result.error}")

    def finish(self, api_rc, job) -> None:
        """Finishes put Upgrade Plan."""
        if api_rc.in_shutdown:
            return

        if not job.result.ok or job.result.body.get("results") is None:
            return

        new_plan_details = job.result.body.get("results").get("subscription")
        plan_info = PoliigonSubscription()
        plan_info.update_from_dict(new_plan_details)
        api_rc._addon.user.plan = plan_info

        api_rc.add_job_get_available_plans(
            callback_done=api_rc._addon_params.callback_get_available_plans)

        api_rc.add_job_get_user_data(
            api_rc._addon.user.user_name,
            api_rc._addon.user.user_id,
            callback_cancel=None,
            callback_progress=None,
            callback_done=api_rc._addon_params.callback_get_user_data_done,
            force=True
        )


@dataclass
class ApiJobParamsResumePlan(ApiJobParams):
    """Get Information for Resuming paused Plan or remove cancellation."""

    POOL_KEY = PoolKeys.INTERACTIVE

    def __eq__(self, other):
        return True

    def __str__(self) -> str:
        return "ApiJobParamsResumePlan"

    def thread_execute(self, api_rc, job) -> None:
        """Executes the request for Resume current Plan."""

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return

        if api_rc._addon.user is None or api_rc._addon.upgrade_manager is None:
            api_rc.logger.error("User not defined when resuming Plan.")
            return

        upgrade_status = api_rc._addon.upgrade_manager.status
        if upgrade_status == PlanUpgradeStatus.RESUME_PLAN:
            job.result = api_rc._addon._api.resume_paused_plan()
        elif upgrade_status == PlanUpgradeStatus.REMOVE_SCHEDULED_PAUSE:
            job.result = api_rc._addon._api.remove_scheduled_paused_plan()
        elif upgrade_status == PlanUpgradeStatus.REMOVE_CANCELLATION:
            job.result = api_rc._addon._api.remove_cancellation_plan()
        else:
            msg = "Invalid Plan Status for resuming."
            api_rc.logger.error(msg)
            job.result.error = msg
            return

        if not job.result.ok:
            api_rc.logger.error(
                f"Error resuming Plan. {job.result.error}")

    def finish(self, api_rc, job) -> None:
        """Finishes get Upgrade Plan, and stores Upgrade information."""

        if api_rc.in_shutdown:
            return

        if not job.result.ok or job.result.body.get("results") is None:
            return

        payload = job.result.body.get("results", {}).get("payload", {})
        subscription_details = payload.get("subscriptionDetails")
        if subscription_details is not None:
            api_rc._addon.user.plan.update_from_dict(subscription_details)

        # Refreshing Upgrade Manager - and only the content success popup with
        # the new data for Subscription Details after resuming
        # (new renewal date)
        api_rc._addon.upgrade_manager.refresh(only_resume_popup=True)

        api_rc.add_job_get_user_data(
            api_rc._addon.user.user_name,
            api_rc._addon.user.user_id,
            callback_cancel=None,
            callback_progress=None,
            callback_done=api_rc._addon_params.callback_get_user_data_done,
            force=True
        )


@dataclass
class ApiJobParamsGetAssets(ApiJobParams):
    """Get Assets specific parameters"""

    library_paths: List[str]
    tab: str  # KEY_TAB_ONLINE or KEY_TAB_MY_ASSETS
    category_list: List[str] = field(default_factory=lambda: [CATEGORY_ALL])
    search: str = ""
    idx_page: int = 1
    page_size: Optional[int] = None
    force_request: bool = False
    do_get_all: bool = True
    ignore_old_names: bool = True
    # Not exactly parameters, more results, may be used in callback_done
    already_in_index: bool = False
    asset_id_list: List[int] = field(default_factory=lambda: [])

    POOL_KEY = PoolKeys.INTERACTIVE

    def __eq__(self, other):
        return self.tab == other.tab and \
            self.category_list == other.category_list and \
            self.search == other.search and \
            self.idx_page == other.idx_page and \
            self.page_size == other.page_size and \
            self.force_request == other.force_request and \
            self.do_get_all == other.do_get_all

    def __str__(self) -> str:
        # No library paths in here, as the string might be reported to server!
        return (
            "ApiJobParamsGetAssets - "
            f"tab: {self.tab}, cat_list: {self.category_list}, "
            f"search: {self.search}, idx_page: {self.idx_page}, "
            f"page_size: {self.page_size}, force: {self.force_request}, "
            f"do_get_all: {self.do_get_all}, "
            f"already_in_index: {self.already_in_index}, "
            f"asset_id_list: {self.asset_id_list}"
        )

    def _get_key(self) -> str:
        """Returns search key for this job."""

        return get_search_key(self.tab, self.search, self.category_list)

    def _determine_page_size(self, api_rc) -> None:
        """Determines 'get asset' page size from API RC's addon parameters."""

        if self.page_size is not None:
            return

        addon_params = api_rc._addon_params
        if self.tab == KEY_TAB_ONLINE:
            self.page_size = addon_params.online_assets_chunk_size
        elif self.tab == KEY_TAB_MY_ASSETS:
            self.page_size = addon_params.my_assets_chunk_size
        else:
            msg = f"Job 'Get Assets': Unknown tab {self.tab}"
            api_rc.logger.error(msg)
            api_rc._addon._api._report_message(
                "get_assets_failed_other", msg, "warning")
            self.page_size = 10  # arbitrary size

    def _map_categories_local_to_api(self) -> List[str]:
        """Maps categories from local/plugin to API convention."""

        # Removing "All Assets" from categories. API expects only the other
        # categories when there are more than one in the list.
        to_map_list = self.category_list
        if len(self.category_list) > 1 and self.category_list[0] == CATEGORY_ALL:
            to_map_list = self.category_list[1:]

        mapped_category_list = [
            CATEGORY_MAPPING_LOCAL_TO_API.get(cat, cat)
            for cat in to_map_list
        ]
        # Remap "virtual free" category to "All Assets" for server
        if mapped_category_list == [CATEGORY_FREE]:
            mapped_category_list = [CATEGORY_ALL]
        return mapped_category_list

    def _get_algolia_query(self) -> Dict:
        """Returns a dict with Algolia search parameters."""

        if "Free" in self.category_list:
            numeric_filters = ["Credit=0"]
        else:
            numeric_filters = ["Credit>=0"]

        mapped_category_list = self._map_categories_local_to_api()
        category_root = mapped_category_list[0]

        if len(mapped_category_list) > 1:
            # TODO(Andreas): strange branch from P4B
            if category_root == CATEGORY_ALL:
                facet_filters = [[]]
                # for asset_type in ["HDRIs", "Models", "Textures"]:  # TODO(Andreas): have constant for ALL_TYPES
                #     if (
                #         f"/{mapped_category_list[1]}"
                #         in self.vCategories[self.tab][asset_type].keys()
                #     ):
                categories = [self.category_list[1]] + mapped_category_list[1:]
                level = len(categories) - 1
                categories = " > ".join(categories)
                facet_filters[0].append(
                    f"RefineCategories.lvl{level}:{categories}"
                )
            else:
                level = len(mapped_category_list) - 1
                categories = " > ".join(mapped_category_list)
                facet_filters = [f"RefineCategories.lvl{level}:{categories}"]
        elif category_root != CATEGORY_ALL:
            facet_filters = [f"RefineCategories.lvl0:{category_root}"]
        else:
            facet_filters = []

        query = {
            "query": self.search,
            "page": self.idx_page,
            "perPage": self.page_size,
            "algoliaParams": {"facetFilters": facet_filters,
                              "numericFilters": numeric_filters
                              },
        }
        return query

    def _update_from_old_filenames(
            self, api_rc, asset_data: AssetData) -> None:
        """Optionally check, if we also find directories with old names
        and update from those accordingly."""

        if self.ignore_old_names:
            return

        old_asset_names = asset_data.old_asset_names
        if old_asset_names is None or len(old_asset_names) == 0:
            return

        for _old_name in old_asset_names:
            dir_asset_old = os.path.join(self.path_library, _old_name)
            if not os.path.isdir(dir_asset_old):
                continue

            api_rc._asset_index.update_from_directory(
                asset_data.asset_id,
                dir_asset_old,
                workflow_fallback="REGULAR"
            )

    def thread_execute(self, api_rc, job) -> None:
        """Executes a get assets job in a thread,
        started from thread_schedule.
        """

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return

        key = self._get_key()
        api_rc.logger.debug(f"Cat/search change: {key}")

        self._determine_page_size(api_rc)

        query_exists = api_rc._asset_index.query_exists(
            key, self.idx_page, self.page_size)
        if query_exists and not self.force_request:
            self.already_in_index = True
            job.result = ApiResponse(ok=True,
                                     body={"data": []},
                                     error="job cancelled, query exists")
            return

        query = self._get_algolia_query()
        if self.tab == KEY_TAB_MY_ASSETS:
            job.result = api_rc._api.get_user_assets(query_data=query)
        else:
            job.result = api_rc._api.get_assets(query_data=query)

    def finish(self, api_rc, job) -> None:
        """Finishes get asset jobs, called from thread_collect."""

        if api_rc.in_shutdown:
            return

        if not job.result.ok or self.already_in_index:
            return

        key = self._get_key()

        api_rc.logger.debug(f"Cat/search change FINISHED: {key}")

        is_later_page = self.idx_page > 1
        asset_id_list = api_rc._asset_index.populate_assets(
            job.result,
            key,
            IDX_PAGE_ACCUMULATED,
            PAGE_SIZE_ACCUMULATED,
            append_query=is_later_page)
        api_rc._asset_index.store_query(
            asset_id_list, key, self.idx_page, self.page_size)

        # Store asset ID list for potential use in done callback
        self.asset_id_list = asset_id_list

        # Optimization: Do only scan local files after "My Asset" requests
        if self.tab == KEY_TAB_MY_ASSETS or api_rc._addon.is_unlimited_user():
            filter_id_list = self.asset_id_list
            if api_rc._addon.is_unlimited_user():
                # TODO(Joao): Implement it in a way that the benefit of filtering
                #  asset id list also works for unlimited users
                filter_id_list = None
            api_rc._asset_index.update_all_local_assets(
                self.library_paths, asset_id_list=filter_id_list)
            for asset_id in asset_id_list:
                asset_data = api_rc._asset_index.get_asset(asset_id)
                self._update_from_old_filenames(api_rc, asset_data)

        job_is_done = self.idx_page >= job.result.body.get("last_page", -1)

        if not self.do_get_all or job_is_done:
            return

        api_rc.add_job_get_assets(
            library_paths=self.library_paths,
            tab=self.tab,
            category_list=self.category_list,
            search=self.search,
            idx_page=self.idx_page + 1,
            page_size=self.page_size,
            force_request=self.force_request,
            do_get_all=self.do_get_all,
            callback_cancel=None,
            callback_progress=None,
            callback_done=job.callback_done,
            force=True)


@dataclass
class ApiJobParamsDownloadThumb(ApiJobParams):
    """Download Thumb specific parameters"""

    asset_id: int
    url: str
    path: str
    do_update: bool = False
    skip_download: bool = False
    idx_thumb: int = -1

    POOL_KEY = PoolKeys.PREVIEW_DL

    def __eq__(self, other):
        return self.url == other.url

    def __str__(self) -> str:
        # No paths in here, as the string might be reported to server!
        return (
            "ApiJobParamsDownloadThumb - "
            f"asset_id: {self.asset_id}, url: {self.url}, "
            f"do_update: {self.do_update}, skip_download: {self.skip_download}"
        )

    def thread_execute(self, api_rc, job) -> None:
        """Executes a download thumb job in a thread,
        started from thread_schedule.
        """

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return

        if not self.do_update and os.path.exists(self.path):
            job.result = ApiResponse(ok=True, body={}, error="")
            return

        try:
            self.skip_download = job.callback_progress(downloading=True,
                                                       job=job)
        except TypeError:
            self.skip_download = False

        if self.skip_download:
            job.result = ApiResponse(ok=True, body={}, error="")
            return

        path_download = f"{self.path}_dl"

        job.result = api_rc._api.download_preview(self.url, path_download)

        # TODO(Andreas): error reporting,
        try:
            if os.path.exists(path_download):
                if os.path.exists(self.path):
                    os.remove(self.path)
                os.rename(path_download, self.path)
        except OSError:  # TODO(Andreas)
            api_rc.logger.exception(f"### rename exc: {self.path}")

    def finish(self, api_rc, job) -> None:
        """Finishes download thumb jobs, called from thread_collect."""

        if api_rc.in_shutdown:
            return

        if self.skip_download:
            return
        try:
            job.callback_progress(downloading=False, job=job)
        except TypeError:
            pass  # nothing to do

        if os.path.isfile(f"{self.path}_temp"):
            os.remove(f"{self.path}_temp")


@dataclass
class ApiJobParamsPurchaseAsset(ApiJobParams):
    """Asset purchase specific parameters"""

    asset_data: AssetData
    category_list: List[str] = field(default_factory=lambda: [CATEGORY_ALL])
    search: str = ""
    # An optional follow-up download job
    job_download: Optional = None  # type ApiJob

    POOL_KEY = PoolKeys.INTERACTIVE

    def __eq__(self, other):
        return self.asset_data.asset_id == other.asset_data.asset_id

    def __str__(self) -> str:
        return (
            "ApiJobParamsPurchaseAsset - "
            f"asset_data (id): {self.asset_data.asset_id}, "
            f"cat_list: {self.category_list}, "
            f"search: {self.search}, job_download: {self.job_download}"
        )

    def _get_category_slug(self) -> str:
        """Gets the slug format of the active category.
        E.g.:
        from ["All Models"] to "/"
        from ["Models", "Bathroom"] to "/models/bathroom"
        and undo transforms of f_GetCategoryChildren.
        """

        # TODO(related to SOFT-762 and SOFT-598):
        #      Refactor f_GetCategoryChildren as part of Core migration.
        category_slug = "/" + "/".join(
            [cat.lower().replace(" ", "-") for cat in self.category_list]
        )
        if category_slug.startswith("/hdris/"):
            category_slug = category_slug.replace("/hdris/", "/hdrs/")
        elif category_slug == "/all-assets":
            category_slug = "/"
        return category_slug

    def thread_execute(self, api_rc, job) -> None:
        """Executes a purchase asset job in a thread,
        started from thread_schedule.
        """

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return

        asset_data = self.asset_data
        asset_id = asset_data.asset_id

        search = self.search.lower()
        category_slug = self._get_category_slug()

        asset_data.state.purchase.start()
        job.result = api_rc._api.purchase_asset(
            asset_id, search, category_slug)

    def finish(self, api_rc, job) -> None:
        """Finishes purchase asset jobs, called from thread_collect."""

        if api_rc.in_shutdown:
            return

        asset_data = self.asset_data
        asset_id = asset_data.asset_id
        if job.result.ok:
            api_rc._asset_index.mark_purchased(asset_id)
            if self.job_download is not None:
                api_rc.enqueue_job(self.job_download)
        else:
            asset_data.state.purchase.set_error(error_msg=job.result.error)
            # See comment in ApiRemoteControl.create_job_download_asset()
            # In order to guarantee immediate feedback to user, the download
            # state already gets set upon creation of the follow-up
            # auto-download job. But this wont be executed in case of a
            # purchase error. Thus the flag needs to be reset, here.
            asset_data.state.dl.end()
            err = job.result.body.get("error", job.result.error)
            api_rc.logger.error((f"Failed to purchase asset {asset_id}"
                                 f"\nerror: {err}"
                                 f"\nbody: {job.result.body}"))
            if ERR_NOT_ENOUGH_CREDITS not in err:
                # "Not enough credits" is already reported earlier
                api_rc._addon._api._report_message(
                    "purchase_failed_other", f"{asset_id}: {err}", "error")

        asset_data.state.purchase.end()

        api_rc._asset_index.flush_queries_by_tab(KEY_TAB_MY_ASSETS)

        # By requesting user data multiple follow up jobs get kicked off
        # (besides updating credits):
        # - Update category data
        # - Update online assets
        #   (under normal conditions already cached -> skipped)
        # - Update my_assets
        # - Update upgrade
        api_rc.add_job_get_user_data(
            api_rc._addon.user.user_name,
            api_rc._addon.user.user_id,
            callback_cancel=None,
            callback_progress=None,
            callback_done=api_rc._addon_params.callback_get_user_data_done,
            force=True
        )


@dataclass
class ApiJobParamsDownloadAsset(ApiJobParams):
    """Asset download specific parameters"""

    download: AssetDownload
    asset_data: AssetData
    size: str
    size_bg: str = ""
    type_bg: str = "EXR"
    lod: str = "NONE"
    variant: str = ""
    download_lods: bool = False
    native_mesh: bool = True
    renderer: str = ""

    POOL_KEY = PoolKeys.ASSET_DL

    def __eq__(self, other):
        return self.asset_data.asset_id == other.asset_data.asset_id and \
            self.size == other.size and \
            self.size_bg == other.size_bg and \
            self.type_bg == other.type_bg and \
            self.lod == other.lod and \
            self.variant == other.variant

    def __str__(self) -> str:
        return (
            "ApiJobParamsDownloadAsset - "
            f"download: {self.download}, size: {self.size}, "
            f"size_bg: {self.size_bg}, type_bg: {self.type_bg}, "
            f"lod: {self.lod}, variant: {self.variant}, "
            f"download_lods: {self.download_lods}, "
            f"native_mesh: {self.native_mesh}, renderer: {self.renderer}"
        )

    def thread_execute(self, api_rc, job) -> None:
        """Executes an asset download job in a thread,
        started from thread_schedule.
        """

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return

        # Wrap to pass job through api
        try:
            partial_progress = partial(job.callback_progress, job)
        except TypeError:
            # No progress callback
            partial_progress = None

        download_dir = api_rc._addon.get_library_path(primary=True)
        valid_sizes = self.asset_data.get_type_data().get_size_list()
        if self.size not in valid_sizes:
            self.size = api_rc._addon.get_type_default_size(self.asset_data)

        self.download = AssetDownload(
            addon=api_rc._addon,
            asset_data=self.asset_data,
            size=self.size,
            dir_target=download_dir,
            download_lods=self.download_lods,
            native_mesh=self.native_mesh,
            renderer=self.renderer,
            update_callback=partial_progress
        )
        result = self.download.kickoff_download()
        job.result = ApiResponse(ok=result,
                                 body={},
                                 error="")

    def finish(self, api_rc, job) -> None:
        """Finishes download asset jobs, called from thread_collect."""

        if api_rc.in_shutdown:
            return

        asset_data = self.asset_data
        asset_id = asset_data.asset_id
        error = asset_data.state.dl.error

        asset_data.state.dl.end()
        if job.result.ok:
            download_dir = asset_data.state.dl.get_directory()
            api_rc._asset_index.update_from_directory(asset_id, download_dir)
            if self.size != "NONE":
                asset_data.runtime.store_current_size(self.size)
            asset_data.state.dl.set_recently_downloaded(True)
        elif error not in [None, ""]:
            job.result.error = asset_data.state.dl.error


@dataclass
class ApiJobParamsDownloadWMPreview(ApiJobParams):
    """Asset download specific parameters"""

    asset_data: AssetData
    renderer: str = ""
    # Not exactly parameters, more results, may be used in callback_done
    files: List[str] = field(default_factory=lambda: [])

    POOL_KEY = PoolKeys.ASSET_DL

    def __eq__(self, other):
        return self.asset_data.asset_id == other.asset_data.asset_id

    def __str__(self) -> str:
        # No files in here, as the string might be reported to server!
        return (
            "ApiJobParamsDownloadWMPreview - "
            f"asset_data (id): {self.asset_data.asset_id}, "
            f"renderer: {self.renderer}"
        )

    def thread_execute(self, api_rc, job) -> None:
        """Executes an download watermarked preview job in a thread,
        started from thread_schedule.
        """

        if api_rc.in_shutdown:
            job.result = get_shutdown_response()
            return

        path_wm_previews = api_rc._addon.get_wm_download_path(
            self.asset_data.asset_name)

        asset_type_data = self.asset_data.get_type_data()
        urls_wm = asset_type_data.get_watermark_preview_url_list()

        files_to_download = []
        if self.asset_data.is_backplate():
            # TODO(Andreas): Untested branch
            path_wm = os.path.join(path_wm_previews,
                                   self.asset_data.asset_name + "_WM.jpg_dl")
            if not os.path.exists(path_wm):
                files_to_download.append((urls_wm[0], path_wm))
        else:
            try:
                os.makedirs(path_wm_previews, exist_ok=True)
            except BaseException:
                # TODO(Andreas)
                api_rc.logger.exception("Failed to create dir for WM previews")

            for url in urls_wm:
                filename_wm_dl = os.path.basename(url.split("?")[0])
                filename_wm_dl += "_dl"
                # Might need to skip certain maps to improve performance
                # if any(vM in vFName for vM in ['BUMP','DISP']+[f'VAR{i}' for i in range(2,9)]) :
                #    continue

                path_wm = os.path.join(path_wm_previews, filename_wm_dl)
                if not os.path.exists(path_wm):
                    files_to_download.append((url, path_wm))

        if len(files_to_download) > 0:
            job.result = api_rc._addon.download_material_wm(files_to_download)
        else:
            job.result = ApiResponse(ok=True, body={}, error="")

    def finish(self, api_rc, job) -> None:
        """Finishes download asset jobs, called from thread_collect."""

        if api_rc.in_shutdown:
            return

        path_wm_previews = api_rc._addon.get_wm_download_path(
            self.asset_data.asset_name)
        asset_id = self.asset_data.asset_id
        api_rc._asset_index.update_from_directory(
            asset_id, path_wm_previews, workflow_fallback="METALNESS")
