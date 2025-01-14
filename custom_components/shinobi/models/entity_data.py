from ..helpers.const import *


class EntityData:
    id: str
    unique_id: str
    name: str
    state: bool
    attributes: dict
    icon: str
    device_name: str
    status: str
    device_class: str
    details: dict
    disabled: bool

    def __init__(self):
        self.id = ""
        self.unique_id = ""
        self.name = ""
        self.state = False
        self.attributes = {}
        self.icon = ""
        self.device_name = ""
        self.status = ENTITY_STATUS_CREATED
        self.device_class = ""
        self.details = {}
        self.disabled = False

    def __repr__(self):
        obj = {
            ENTITY_ID: self.id,
            ENTITY_UNIQUE_ID: self.unique_id,
            ENTITY_NAME: self.name,
            ENTITY_STATE: self.state,
            ENTITY_ATTRIBUTES: self.attributes,
            ENTITY_ICON: self.icon,
            ENTITY_DEVICE_NAME: self.device_name,
            ENTITY_STATUS: self.status,
            ENTITY_DEVICE_CLASS: self.device_class,
            ENTITY_CAMERA_DETAILS: self.details,
            ENTITY_DISABLED: self.disabled,
        }

        to_string = f"{obj}"

        return to_string
