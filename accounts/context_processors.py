def notifications_count(request):
    """
    Injecte le nombre de notifications non lues dans tous les templates.
    Disponible via {{ nb_notifs_sidebar }} partout.
    """
    if request.user.is_authenticated:
        try:
            count = request.user.notifications.filter(lue=False).count()
        except Exception:
            count = 0
        return {'nb_notifs_sidebar': count}
    return {'nb_notifs_sidebar': 0}