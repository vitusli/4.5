# #### BEGIN GPL LICENSE BLOCK #####
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

import datetime

from .modules.poliigon_core.multilingual import _t
from .modules.poliigon_core.notifications import (
    NOTICE_ICON_WARN,
    NOTICE_PRIO_MEDIUM,
    NotificationPopup)
from .constants import URLS_BLENDER


def build_lost_client_notification(cTB) -> None:
    msg = ("Asset Browser synchronization client exited unexpectedly.")
    notice = NotificationPopup(
        id_notice="ASSET_BROWSER_LOST_CLIENT",
        title=msg,
        label=msg,
        priority=NOTICE_PRIO_MEDIUM,
        allow_dismiss=True,
        open_popup=True,
        tooltip=msg,
        icon=cTB.notify.icon_dcc_map[NOTICE_ICON_WARN],
        body=msg
    )
    cTB.notify.enqueue_notice(notice)


def build_new_catalogue_notification(cTB) -> None:
    # TODO(Andreas): Notification temporarily disabled, when changing to P4BAC.
    #                Might reappear as popup.
    return
    title = "Reload file to update asset browser catalogues."
    msg = ("We created a new catalogue file for Poliigon Library in Asset "
           "Browser. Unfortunately Blender will pick up the new catalogues "
           "only after either reloading the current blend file or restarting "
           "Blender.")
    notice = NotificationPopup(
        id_notice="ASSET_BROWSER_LOST_CLIENT",
        title=title,
        label=msg,
        priority=NOTICE_PRIO_MEDIUM,
        allow_dismiss=True,
        open_popup=True,
        tooltip=msg,
        icon=cTB.notify.icon_dcc_map[NOTICE_ICON_WARN],
        body=msg
    )
    cTB.notify.enqueue_notice(notice)


def build_no_internet_notification(cTB) -> None:
    msg = _t(
        "Please connect to the internet to continue using the Poliigon "
        "Addon."
    )
    cTB.notify.create_no_internet(tooltip=msg)


def build_no_refresh_notification(cTB) -> None:
    title = "Sync done, press refresh in asset browser."
    msg = ("Failed to refresh the Poliigon Library in Asset Browser. "
           "Either press the Refresh Library button in Asset Browser or "
           "consider a restart of Blender.")
    notice = NotificationPopup(
        id_notice="ASSET_BROWSER_LOST_CLIENT",
        title=title,
        label=msg,
        priority=NOTICE_PRIO_MEDIUM,
        allow_dismiss=True,
        open_popup=True,
        tooltip=msg,
        icon=cTB.notify.icon_dcc_map[NOTICE_ICON_WARN],
        body=msg
    )
    cTB.notify.enqueue_notice(notice)


# TODO(Andreas): was used by legacy importer, only
def build_material_template_error_notification(cTB) -> None:
    msg = _t(
        "Failed to load the material template file.\n"
        "Please remove the addon, restart blender,\n"
        "and re-install the latest version of the addon.\n"
        "Please reach out to support if you continue to have issues at "
        "help.poliigon.com"
    )
    cTB.notify.create_write_mat_template(tooltip=msg, body=msg)


def build_proxy_notification(cTB) -> None:
    msg = _t(
        "Error: Blender cannot connect to the internet.\n"
        "Disable network proxy or firewalls."
    )
    cTB.notify.create_proxy(tooltip=msg, body=msg)


def build_restart_notification(cTB) -> None:
    cTB.notify.create_restart_needed(
        title=_t("Restart Blender"),
        tooltip=_t("Please restart Blender to complete the update"),
        action_string="wm.quit_blender"
    )


def build_survey_notification(cTB) -> None:
    cTB.notify.create_survey(
        is_free_user=cTB.is_free_user(),
        tooltip=_t("Share your feedback so we can improve this addon for you"),
        free_survey_url=URLS_BLENDER["survey_free"],
        active_survey_url=URLS_BLENDER["survey_subscribed"],
        label=_t("Let us know"),
        # on_dismiss_callable=None
    )


def get_datetime_now():
    return datetime.datetime.now(datetime.timezone.utc)


def add_survey_notification(cTB) -> bool:
    """Registers a survey notification, if conditions are met.

    NOTE: To be called via self.f_add_survey_notifcation_once().
          This function will overwrite this function reference
          member variable in order to deactivate itself.

    Return value:
    True, if settings should be saved afterwards.
    Since we can't call save_settings() here due to circular
    imports.
    """

    # DISABLE this very function we are in.
    cTB.f_add_survey_notifcation_once = lambda: None

    if not cTB._any_local_assets():
        # Do not bother users, who haven't downloaded anything, yet
        return False

    already_asked = "last_nps_ask" in cTB.settings
    already_opened = "last_nps_open" in cTB.settings
    if already_asked or already_opened:
        # Never bother the user twice
        return False

    # 7 day period starts after first local assets got detected
    time_now = get_datetime_now()
    if "first_local_asset" not in cTB.settings:
        cTB.settings["first_local_asset"] = time_now.timestamp()
        return True

    ts_first_local = cTB.settings["first_local_asset"]
    time_first_local = datetime.datetime.fromtimestamp(
        ts_first_local, datetime.timezone.utc)
    time_since = time_now - time_first_local
    if time_since.days < 7:
        return False

    build_survey_notification(cTB)
    cTB.settings["last_nps_ask"] = time_now.timestamp()
    return True


def build_writing_settings_failed_notification(cTB, error_string: str) -> None:
    msg = _t("Error: Failed to write its settings: {0}").format(error_string)

    cTB.notify.create_write_settings_error(tooltip=msg, body=msg)
