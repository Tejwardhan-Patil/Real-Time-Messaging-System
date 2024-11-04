from enum import Enum
from typing import List, Dict, Optional

class Role(Enum):
    ADMIN = "Admin"
    MODERATOR = "Moderator"
    USER = "User"
    GUEST = "Guest"

class Permission(Enum):
    CREATE_MESSAGE = "create_message"
    EDIT_MESSAGE = "edit_message"
    DELETE_MESSAGE = "delete_message"
    VIEW_MESSAGE = "view_message"
    MANAGE_USERS = "manage_users"
    ASSIGN_ROLES = "assign_roles"
    BAN_USER = "ban_user"

# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.ADMIN: [
        Permission.CREATE_MESSAGE,
        Permission.EDIT_MESSAGE,
        Permission.DELETE_MESSAGE,
        Permission.VIEW_MESSAGE,
        Permission.MANAGE_USERS,
        Permission.ASSIGN_ROLES,
        Permission.BAN_USER,
    ],
    Role.MODERATOR: [
        Permission.CREATE_MESSAGE,
        Permission.EDIT_MESSAGE,
        Permission.DELETE_MESSAGE,
        Permission.VIEW_MESSAGE,
        Permission.BAN_USER,
    ],
    Role.USER: [
        Permission.CREATE_MESSAGE,
        Permission.EDIT_MESSAGE,
        Permission.VIEW_MESSAGE,
    ],
    Role.GUEST: [
        Permission.VIEW_MESSAGE
    ]
}

class PermissionDeniedError(Exception):
    """Exception raised when a user does not have permission to perform an action."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class User:
    def __init__(self, user_id: str, role: Role):
        self.user_id = user_id
        self.role = role

class PermissionsManager:
    def __init__(self):
        self.user_roles: Dict[str, Role] = {}
        self.user_permissions: Dict[str, List[Permission]] = {}

    def assign_role(self, user_id: str, role: Role):
        """Assign a role to a user."""
        self.user_roles[user_id] = role
        self.user_permissions[user_id] = ROLE_PERMISSIONS[role]
    
    def get_user_role(self, user_id: str) -> Optional[Role]:
        """Retrieve the role assigned to a user."""
        return self.user_roles.get(user_id)
    
    def check_permission(self, user_id: str, permission: Permission):
        """Check if the user has the required permission."""
        user_permissions = self.user_permissions.get(user_id)
        if not user_permissions or permission not in user_permissions:
            raise PermissionDeniedError(f"User {user_id} does not have {permission} permission.")
    
    def list_permissions(self, user_id: str) -> List[Permission]:
        """List all permissions available to the user."""
        return self.user_permissions.get(user_id, [])

    def update_user_permissions(self, user_id: str, permissions: List[Permission]):
        """Update permissions of a user directly."""
        if user_id in self.user_permissions:
            self.user_permissions[user_id] = permissions
        else:
            raise PermissionDeniedError(f"User {user_id} not found.")

# Use case with session management
class SessionManager:
    def __init__(self, permission_manager: PermissionsManager):
        self.active_sessions: Dict[str, User] = {}
        self.permission_manager = permission_manager
    
    def login(self, user_id: str, role: Role):
        """Simulate user login and assign role."""
        user = User(user_id, role)
        self.active_sessions[user_id] = user
        self.permission_manager.assign_role(user_id, role)
    
    def logout(self, user_id: str):
        """Simulate user logout."""
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
        else:
            raise ValueError(f"User {user_id} is not logged in.")

    def perform_action(self, user_id: str, action: Permission):
        """Perform an action that requires permission."""
        if user_id in self.active_sessions:
            self.permission_manager.check_permission(user_id, action)
            print(f"User {user_id} performed action: {action.name}")
        else:
            raise PermissionDeniedError(f"User {user_id} is not logged in or doesn't exist.")

# RBAC system initialized
permissions_manager = PermissionsManager()
session_manager = SessionManager(permissions_manager)

# Assign some roles and test actions
session_manager.login("user123", Role.ADMIN)
session_manager.login("user456", Role.MODERATOR)

# Performing actions as Admin
try:
    session_manager.perform_action("user123", Permission.CREATE_MESSAGE)
    session_manager.perform_action("user123", Permission.BAN_USER)
except PermissionDeniedError as e:
    print(e)

# Performing actions as Moderator
try:
    session_manager.perform_action("user456", Permission.CREATE_MESSAGE)
    session_manager.perform_action("user456", Permission.BAN_USER)  # This should succeed
    session_manager.perform_action("user456", Permission.MANAGE_USERS)  # This should fail
except PermissionDeniedError as e:
    print(e)

# Trying to assign an invalid role
try:
    session_manager.login("user789", Role.GUEST)
    session_manager.perform_action("user789", Permission.CREATE_MESSAGE)
except PermissionDeniedError as e:
    print(e)

# Function to list all permissions for a user
def list_user_permissions(user_id: str):
    permissions = permissions_manager.list_permissions(user_id)
    if permissions:
        print(f"User {user_id} has permissions: {[p.name for p in permissions]}")
    else:
        print(f"User {user_id} has no permissions assigned.")

# List permissions for users
list_user_permissions("user123")
list_user_permissions("user456")
list_user_permissions("user789")

# Logout users
session_manager.logout("user123")
session_manager.logout("user456")