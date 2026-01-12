import os
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders
import re

def link_callback(uri, rel):
    """
    Converte URIs HTML para caminhos absolutos do sistema para o xhtml2pdf.
    """
    if settings.MEDIA_URL and uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif settings.STATIC_URL and uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:
        result = finders.find(uri)
        if result:
            if not isinstance(result, (list, tuple)):
                result = [result]
            result = list(os.path.normpath(x) for x in result)
            origin = result[0]
            return origin
        return uri

    return path

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    else:
        print(f"Erro Geracao PDF: {pdf.err}")
        return HttpResponse(f"Erro ao gerar PDF: {pdf.err}", status=500)
    return None

def formatar_numero_telefone(telefone):
    """
    Formata número para +258xxxxxxxxx.
    """
    # Remove espaços e caracteres não numéricos (exceto +)
    clean_phone = ''.join(c for c in telefone if c.isdigit() or c == '+')
    
    if not clean_phone.startswith('+'):
        # Se começa com 8 e tem 9 digitos (ex: 841234567), adiciona +258
        if len(clean_phone) == 9 and clean_phone.startswith('8'):
            return f"+258{clean_phone}"
        # Se começa com 258, adiciona +
        elif clean_phone.startswith('258'):
            return f"+{clean_phone}"
        else:
            # Fallback: adiciona +258
            return f"+258{clean_phone}"
    
    return clean_phone

def despachante_login(user):
    """
    Redireciona utilizador logado.
    Admin/Staff -> Painel de Controlo
    Candidatos (se tiverem user) -> Dashboard
    """
    if user.is_staff or user.is_superuser:
        return 'candidaturas:painel_controlo'
    return 'candidaturas:inicio'
