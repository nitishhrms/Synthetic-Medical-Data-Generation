"""
Seed Default Roles and Permissions
Run this after database migration to populate initial RBAC data
"""
import sys
from sqlalchemy.orm import Session
from datetime import datetime
import models
import database

# Default roles configuration
DEFAULT_ROLES = [
    {
        "name": "admin",
        "display_name": "Administrator",
        "description": "Full system access with user management capabilities",
        "is_system_role": True,
        "permissions": [
            "can_manage_users",
            "can_manage_roles",
            "can_view_audit_logs",
            "can_generate_data",
            "can_decrypt_phi",
            "can_export_data",
            "can_import_data",
            "can_view_analytics",
            "can_manage_studies"
        ]
    },
    {
        "name": "researcher",
        "display_name": "Researcher",
        "description": "Can generate and analyze synthetic data",
        "is_system_role": True,
        "permissions": [
            "can_generate_data",
            "can_view_analytics",
            "can_export_data",
            "can_view_studies"
        ]
    },
    {
        "name": "data_analyst",
        "display_name": "Data Analyst",
        "description": "Advanced analytics and PHI access",
        "is_system_role": True,
        "permissions": [
            "can_view_analytics",
            "can_decrypt_phi",
            "can_export_data",
            "can_generate_data",
            "can_view_studies"
        ]
    },
    {
        "name": "viewer",
        "display_name": "Viewer",
        "description": "Read-only access to studies and analytics",
        "is_system_role": True,
        "permissions": [
            "can_view_studies",
            "can_view_analytics"
        ]
    },
    {
        "name": "auditor",
        "display_name": "Auditor",
        "description": "Can view audit logs and security reports",
        "is_system_role": True,
        "permissions": [
            "can_view_audit_logs",
            "can_view_security_reports"
        ]
    }
]

# All permissions in the system
ALL_PERMISSIONS = [
    # User Management
    {
        "name": "can_manage_users",
        "display_name": "Manage Users",
        "description": "Create, update, and delete user accounts",
        "resource_type": "user",
        "action": "manage"
    },
    {
        "name": "can_manage_roles",
        "display_name": "Manage Roles",
        "description": "Assign and revoke user roles",
        "resource_type": "role",
        "action": "manage"
    },

    # Data Generation
    {
        "name": "can_generate_data",
        "display_name": "Generate Data",
        "description": "Generate synthetic medical data",
        "resource_type": "data",
        "action": "create"
    },

    # PHI Access
    {
        "name": "can_decrypt_phi",
        "display_name": "Decrypt PHI",
        "description": "Decrypt protected health information",
        "resource_type": "phi",
        "action": "decrypt"
    },

    # Data Operations
    {
        "name": "can_export_data",
        "display_name": "Export Data",
        "description": "Export data to various formats",
        "resource_type": "data",
        "action": "export"
    },
    {
        "name": "can_import_data",
        "display_name": "Import Data",
        "description": "Import data from external sources",
        "resource_type": "data",
        "action": "import"
    },

    # Analytics
    {
        "name": "can_view_analytics",
        "display_name": "View Analytics",
        "description": "View statistical analysis and reports",
        "resource_type": "analytics",
        "action": "read"
    },

    # Study Management
    {
        "name": "can_manage_studies",
        "display_name": "Manage Studies",
        "description": "Create, update, and delete studies",
        "resource_type": "study",
        "action": "manage"
    },
    {
        "name": "can_view_studies",
        "display_name": "View Studies",
        "description": "View study information",
        "resource_type": "study",
        "action": "read"
    },

    # Audit & Security
    {
        "name": "can_view_audit_logs",
        "display_name": "View Audit Logs",
        "description": "Access audit trail and security logs",
        "resource_type": "audit",
        "action": "read"
    },
    {
        "name": "can_view_security_reports",
        "display_name": "View Security Reports",
        "description": "View security incidents and reports",
        "resource_type": "security",
        "action": "read"
    }
]


def seed_permissions(db: Session) -> dict:
    """Create all permissions"""
    permissions_map = {}

    for perm_data in ALL_PERMISSIONS:
        # Check if permission already exists
        existing = db.query(models.Permission).filter(
            models.Permission.name == perm_data["name"]
        ).first()

        if existing:
            print(f"  ✓ Permission '{perm_data['name']}' already exists")
            permissions_map[perm_data["name"]] = existing
            continue

        # Create new permission
        permission = models.Permission(
            name=perm_data["name"],
            display_name=perm_data["display_name"],
            description=perm_data["description"],
            resource_type=perm_data.get("resource_type"),
            action=perm_data.get("action")
        )
        db.add(permission)
        permissions_map[perm_data["name"]] = permission
        print(f"  + Created permission: {perm_data['name']}")

    db.commit()
    print(f"\n✅ Seeded {len(permissions_map)} permissions")
    return permissions_map


def seed_roles(db: Session, permissions_map: dict):
    """Create all roles and assign permissions"""

    for role_data in DEFAULT_ROLES:
        # Check if role already exists
        existing = db.query(models.Role).filter(
            models.Role.name == role_data["name"]
        ).first()

        if existing:
            print(f"  ✓ Role '{role_data['name']}' already exists")
            role = existing
        else:
            # Create new role
            role = models.Role(
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                is_system_role=role_data["is_system_role"]
            )
            db.add(role)
            db.flush()  # Get role ID
            print(f"  + Created role: {role_data['name']}")

        # Assign permissions to role
        existing_perms = {rp.permission.name for rp in role.permissions}

        for perm_name in role_data["permissions"]:
            if perm_name in existing_perms:
                continue

            if perm_name not in permissions_map:
                print(f"  ⚠️  Warning: Permission '{perm_name}' not found for role '{role_data['name']}'")
                continue

            # Create role-permission association
            role_permission = models.RolePermission(
                role_id=role.id,
                permission_id=permissions_map[perm_name].id
            )
            db.add(role_permission)
            print(f"    → Assigned '{perm_name}' to '{role_data['name']}'")

    db.commit()
    print(f"\n✅ Seeded {len(DEFAULT_ROLES)} roles with permissions")


def migrate_existing_users(db: Session):
    """Assign roles to existing users based on their 'role' column"""
    users = db.query(models.User).all()

    if not users:
        print("\nℹ️  No existing users to migrate")
        return

    print(f"\n📋 Migrating {len(users)} existing users to RBAC...")

    roles_cache = {role.name: role for role in db.query(models.Role).all()}

    for user in users:
        # Check if user already has role assignments
        if user.user_roles:
            print(f"  ✓ User '{user.username}' already has role assignments")
            continue

        # Get role from old 'role' column
        role_name = user.role or "viewer"  # Default to viewer if no role

        if role_name not in roles_cache:
            print(f"  ⚠️  User '{user.username}' has unknown role '{role_name}', assigning 'viewer'")
            role_name = "viewer"

        # Create role assignment
        user_role = models.UserRole(
            user_id=user.id,
            role_id=roles_cache[role_name].id,
            assigned_at=datetime.utcnow()
        )
        db.add(user_role)
        print(f"  + Assigned '{role_name}' role to user '{user.username}'")

    db.commit()
    print(f"\n✅ Migrated existing users to RBAC")


def main():
    """Run the seed process"""
    print("=" * 60)
    print("🌱 SEEDING ROLES AND PERMISSIONS")
    print("=" * 60)

    # Create database session
    db = database.SessionLocal()

    try:
        print("\n1️⃣  Seeding Permissions...")
        permissions_map = seed_permissions(db)

        print("\n2️⃣  Seeding Roles...")
        seed_roles(db, permissions_map)

        print("\n3️⃣  Migrating Existing Users...")
        migrate_existing_users(db)

        print("\n" + "=" * 60)
        print("✅ SEED COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nDefault roles created:")
        for role in DEFAULT_ROLES:
            print(f"  • {role['name']}: {role['description']}")

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
