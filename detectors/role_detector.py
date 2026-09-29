"""
RobinShield privileged-role detector.

Detects common role-based access-control functions exposed
through the contract ABI.

This detector reports the presence of role-management
mechanisms. It does not assume that a role is dangerous
without evidence of what the role can control.
"""


ROLE_FUNCTIONS = {
    "grantrole",
    "revokerole",
    "renouncerole",
    "hasrole",
    "getroleadmin",
    "getrolemember",
    "getrolemembercount",
}

ADMIN_ROLE_NAMES = {
    "defaultadminrole",
    "adminrole",
    "administratorrole",
    "ownerrole",
}


def _normalize(name):
    if not name:
        return ""

    return (
        str(name)
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
        .lower()
    )


def _function_names(functions):

    if functions is None:
        return []

    names = []

    if isinstance(functions, dict):

        iterable = functions.values()

    else:

        iterable = functions

    try:

        for item in iterable:

            if isinstance(item, str):

                names.append(item)
                continue

            if isinstance(item, dict):

                name = item.get(
                    "name",
                    item.get(
                        "function",
                        "",
                    ),
                )

                if name:
                    names.append(
                        str(name)
                    )
                continue

            name = getattr(
                item,
                "name",
                None,
            )

            if name:
                names.append(
                    str(name)
                )

    except Exception:

        return []

    return names


def scan(functions):

    names = _function_names(
        functions
    )

    role_functions = []
    admin_functions = []

    for name in names:

        normalized = _normalize(
            name
        )

        if normalized in ROLE_FUNCTIONS:

            role_functions.append(
                name
            )

        if normalized in {
            "grantrole",
            "revokerole",
            "renouncerole",
            "getroleadmin",
        }:

            admin_functions.append(
                name
            )

    role_functions = sorted(
        set(role_functions)
    )

    admin_functions = sorted(
        set(admin_functions)
    )

    if not role_functions:

        return {
            "check": "Privileged Roles",
            "status": "PASS",
            "confidence": "MEDIUM",
            "reason": (
                "No recognized role-based access-control "
                "functions were detected."
            ),
        }

    if admin_functions:

        return {
            "check": "Privileged Roles",
            "status": "WARNING",
            "confidence": "MEDIUM",
            "reason": (
                "Role-based access-control functions detected: "
                + ", ".join(
                    role_functions
                )
                + ". Administrative role management may "
                  "exist."
            ),
        }

    return {
        "check": "Privileged Roles",
        "status": "INFO",
        "confidence": "MEDIUM",
        "reason": (
            "Role-related functions detected: "
            + ", ".join(
                role_functions
            )
            + "."
        ),
    }