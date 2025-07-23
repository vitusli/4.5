# ##### BEGIN GPL LICENSE BLOCK #####
#
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


import logging
import queue
from typing import Tuple

import bpy
from bpy.app.handlers import persistent

bk_logger = logging.getLogger(__name__)


def get_largest_area(context=None, area_type='VIEW_3D'):
    maxsurf = 0
    maxa = None
    maxw = None
    region = None
    if context is None:
        windows = bpy.data.window_managers[0].windows
    else:
        windows = context.window_manager.windows
    for w in windows:
        for a in w.screen.areas:
            if a.type == area_type:
                asurf = a.width * a.height
                if asurf > maxsurf:
                    maxa = a
                    maxw = w
                    maxsurf = asurf

                    region = a.regions[-1]
                    # for r in a.regions:
                    #     if r.type == 'WINDOW':
                    #         region = r

    if maxw is None or maxa is None:
        return None, None, None
    return maxw, maxa, region


def get_fake_context(context=None, area_type='VIEW_3D'):
    C_dict = {}  # context.copy() #context.copy was a source of problems - incompatibility with addons that also
    # define context
    C_dict.update(region='WINDOW')

    # if hasattr(context,'window') and hasattr(context,'screen') and hasattr(context,'area') and hasattr(context,
    # 'region'): w = context.window s = context.screen a = context.area r = context.region if not None in (w, s, a,
    # r) and a.type == area_type and r.type == 'WINDOW': override = {'window': w, 'screen': s, 'area': a, 'region': r}
    #
    #         C_dict.update(override)
    #         print('returning almost original context')
    #         return C_dict

    # new context
    w, a, r = get_largest_area(context=context, area_type=area_type)
    if w:
        # sometimes there is no area of the requested type. Let's face it, some people use Blender without 3d view.
        override = {'window': w,
                    'screen': w.screen,
                    'area': a,
                    "space_data": a.spaces.active,
                    'region': r}

        C_dict.update(override)
    return C_dict


@persistent
def scene_load(context):
    if not (bpy.app.timers.is_registered(queue_worker)):
        bpy.app.timers.register(queue_worker)


def get_queue():
    # we pick just a random one of blender types, to try to get a persistent queue
    t = bpy.types.Scene

    if not hasattr(t, 'task_queue'):
        t.task_queue = queue.Queue()
    return t.task_queue


class task_object:
    def __init__(self, command='', arguments=(), wait=0, only_last=False, fake_context=False,
                 fake_context_area='VIEW_3D'):
        self.command = command
        self.arguments = arguments
        self.wait = wait
        self.only_last = only_last
        self.fake_context = fake_context
        self.fake_context_area = fake_context_area


def add_task(task: Tuple, wait=0, only_last=False, fake_context=False, fake_context_area='VIEW_3D'):
    q = get_queue()
    taskob = task_object(task[0], task[1], wait=wait, only_last=only_last, fake_context=fake_context,
                         fake_context_area=fake_context_area)
    q.put(taskob)


# @bpy.app.handlers.persistent
def queue_worker():
    # utils.p('start queue worker timer')

    # bk_logger.debug('timer queue worker')
    time_step = .3
    q = get_queue()

    # save some performance by returning early
    if q.empty():
        return time_step

    back_to_queue = []  # delayed events
    stashed = {}
    # first round we get all tasks that are supposed to be stashed and run only once (only_last option)
    # stashing finds tasks with the property only_last and same command and executes only the last one.
    while not q.empty():
        # print('queue while 1')

        task = q.get()
        print('Task !!: ' + str(task.command))
        if task.only_last:
            # this now makes the keys not only by task, but also first argument.
            # by now stashing is only used for ratings, where the first argument is url.
            # This enables fast rating of multiple assets while allowing larger delay for uploading of ratings.
            # this avoids a duplicate request error on the server
            stashed[str(task.command) + str(task.arguments[0])] = task
        else:
            back_to_queue.append(task)
    if len(stashed.keys()) > 1:
        bk_logger.debug('task queue stashed task:' + str(stashed))
    # return tasks to que except for stashed
    for task in back_to_queue:
        q.put(task)
    # return stashed tasks to queue
    for k in stashed.keys():
        q.put(stashed[k])
    # second round, execute or put back waiting tasks.
    back_to_queue = []
    while not q.empty():
        # print('window manager', bpy.context.window_manager)
        task = q.get()

        if task.wait > 0:
            task.wait -= time_step
            back_to_queue.append(task)
        else:
            bk_logger.debug('task queue task:' + str(task.command) + str(task.arguments))
            try:
                if task.fake_context:
                    fc = get_fake_context(bpy.context, area_type=task.fake_context_area)
                    task.command(fc, *task.arguments)
                else:
                    task.command(*task.arguments)
            except Exception as e:
                bk_logger.error('task queue failed task:' + str(task.command) + str(task.arguments) + str(e))
                # bk_logger.exception('Got exception on main handler')
                # raise
        # print('queue while 2')
    for task in back_to_queue:
        q.put(task)
    # utils.p('end queue worker timer')

    return time_step


def register():
    bpy.app.handlers.load_post.append(scene_load)


def unregister():
    bpy.app.handlers.load_post.remove(scene_load)
