
from . system import printd

class Settings:

    _properties = {}
    _prop_names = {}

    def _get_full_idname(self, idname:str):
        if not idname.startswith('MACHIN3_OT_'):
            idname = f'MACHIN3_OT_{idname}'

        return idname

    def init_settings(self, props=[]):
        idname = self.bl_idname

        if idname not in self._properties:
            self._properties[idname] = {}

        if idname not in self._prop_names:
            self._prop_names[idname] = []

        for name in props:
            if name not in self._prop_names[idname]:
                self._prop_names[idname].append(name)

    def save_settings(self):
        prop_names = self._prop_names[self.bl_idname]

        for name in dir(self.properties):
            if name in prop_names:
                try:
                    self._properties[self.bl_idname][name] = getattr(self.properties, name)
                except:
                    pass

    def store_settings(self, idname:str, data:dict):
        idname = self._get_full_idname(idname)

        if props := self._properties.get(idname):
            for name, prop in data.items():
                props[name] = prop

        else:
            self._properties[idname] = data

    def load_settings(self):
        props = self._properties[self.bl_idname]

        for name in props:
            self.properties[name] = props[name]

    def fetch_setting(self, idname:str, prop:str):
        idname = self._get_full_idname(idname)

        if props := self._properties.get(idname):
            return props.get(prop, None)

    def debug_settings(self, idname:str):
        idname = self._get_full_idname(idname)

        print()
        print("Settings for", idname, "- called from", self.bl_idname)

        if prop_names := self._prop_names.get(idname):
            print("initialized prop names:")

            for name in prop_names:
                print("", name)

        if props := self._properties.get(idname):
            printd(props, name="settings")
