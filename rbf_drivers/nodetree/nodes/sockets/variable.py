


# socket holds reference to source node + socket name and (latest) value
# 




class RBFDataSocket(NodeSocket):

    format: EnumProperty(
        items=[
            ('REF'),
            ('VAL'),
            ('VAR'),
            ]
        )