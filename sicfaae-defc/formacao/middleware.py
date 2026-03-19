"""
Middleware que obriga o utilizador a alterar a senha
antes de aceder a qualquer parte do sistema,
caso o flag deve_alterar_senha esteja activo no seu perfil.
"""

CHANGE_PASSWORD_URL = '/formacao/alterar-senha/'
EXEMPT_URLS = [
    '/accounts/login/',
    '/accounts/logout/',
    CHANGE_PASSWORD_URL,
]


class ForcarAlteracaoSenhaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            # Verificar se o utilizador tem perfil e se deve alterar senha
            try:
                perfil = request.user.perfil
                if perfil.deve_alterar_senha:
                    # Permitir apenas URLs isentas
                    path = request.path_info
                    if not any(path.startswith(url) for url in EXEMPT_URLS):
                        from django.shortcuts import redirect
                        return redirect(CHANGE_PASSWORD_URL)
            except Exception:
                pass

        return self.get_response(request)
