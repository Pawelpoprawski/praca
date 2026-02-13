from fastapi import HTTPException, status


def require_role(*allowed_roles: str):
    def checker(current_user):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Brak uprawnień do tej operacji",
            )
        return current_user
    return checker


def require_worker(current_user):
    if current_user.role != "worker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dostęp tylko dla pracowników",
        )
    return current_user


def require_employer(current_user):
    if current_user.role != "employer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dostęp tylko dla pracodawców",
        )
    return current_user


def require_admin(current_user):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dostęp tylko dla administratorów",
        )
    return current_user
