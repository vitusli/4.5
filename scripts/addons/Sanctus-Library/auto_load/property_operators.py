import bpy.types as bt

from . import props
from . import ops
from . import reg

class PropertyOperator(ops.Operator):
    bl_options = {'UNDO'}

    parent = props.ContextProperty()
    property_attr = props.StringProperty()
    description_text = props.StringProperty()

    @property
    def prop(self) -> props.Property:
        return getattr(self.parent(), self.property_attr())

    def description(self, context: bt.Context) -> str:
        if self.description_text() != '':
            return self.description_text()
        return ops.Operator.description(self, context)
    
    def invoke(self, context: bt.Context, event: bt.Event) -> set[str]:
        self.invoke_event = event
        return super().invoke(context, event)


class CollectionOperator(PropertyOperator):

    @property
    def collection(self) -> props.CollectionProperty:
        return super().prop

@reg.register_operator
class AddCollectionElement(CollectionOperator):

    def run(self, context: bt.Context):
        self.collection.new_from_operator(self.collection, context, self.invoke_event)
    
@reg.register_operator
class RemoveCollectionElement(CollectionOperator):

    element = props.ContextProperty()

    def run(self, context: bt.Context):
        self.collection.remove_from_operator(self.collection, self.element(), context, self.invoke_event)
