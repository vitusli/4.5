import bpy


def draw_layers_header(self, context, RR):
    pass

def draw_layers_header_preset(self, context, RR):
    try:
        #group_name = RR.group.name
        layer_name = RR.props_pre.layer_name
    except:
        #group_name = ''
        layer_name = ''
    row = self.layout.row()
    row.enabled = False
    #row.label(text=group_name)
    row.label(text=layer_name)


def draw_values_header(self, context, RR):
    pass

def draw_values_header_preset(self, context, RR):
    row = self.layout.row(align=True)
    row.enabled = RR.props_pre.use_layer
    if RR.use_values:
        row.prop(RR.props_pre, 'use_values', text="", icon="CHECKBOX_HLT", emboss=False)
    else:
        row.prop(RR.props_pre, 'use_values', text="", icon="CHECKBOX_DEHLT", emboss=False)


def draw_colors_header(self, context, RR):
    pass

def draw_colors_header_preset(self, context, RR):
    row = self.layout.row(align=True)
    row.enabled = RR.props_pre.use_layer
    if RR.use_colors:
        row.prop(RR.props_pre, 'use_colors', text="", icon="CHECKBOX_HLT", emboss=False)
    else:
        row.prop(RR.props_pre, 'use_colors', text="", icon="CHECKBOX_DEHLT", emboss=False)


def draw_effects_header(self, context, RR):
    pass

def draw_effects_header_preset(self, context, RR):
    row = self.layout.row(align=True)
    row.enabled = RR.props_pre.use_layer
    if RR.use_effects:
        row.prop(RR.props_pre, 'use_effects', text="", icon="CHECKBOX_HLT", emboss=False)
    else:
        row.prop(RR.props_pre, 'use_effects', text="", icon="CHECKBOX_DEHLT", emboss=False)
