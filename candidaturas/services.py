import logging
from decouple import config
from .utils import formatar_numero_telefone

logger = logging.getLogger(__name__)

class ServicoWhatsApp:
    @staticmethod
    def is_configured():
        return config('WHATSAPP_API_KEY', default=None) is not None

    @staticmethod
    def enviar_mensagens_massa(queryset, modelo_mensagem):
        """
        Envia mensagens para um queryset de candidatos.
        Se WHATSAPP_API_KEY estiver definido, tenta envio real (placeholder).
        Caso contrário, usa Mock logging.
        """
        api_key = config('WHATSAPP_API_KEY', default=None)
        api_url = config('WHATSAPP_API_URL', default='https://api.whatsapp.provider.com/send')
        
        resultados = {'sucesso': 0, 'falhas': 0}
        modo = "REAL" if api_key else "MOCK"
        
        logger.info(f"Iniciando envio em massa. Modo: {modo}")
        
        for candidato in queryset:
            try:
                telefone = formatar_numero_telefone(candidato.numero_telefone)
                msg = modelo_mensagem.format(name=candidato.nome_completo)
                
                if api_key:
                    # TODO: Implementar request.post(api_url, json={...})
                    # Simulação devolução da API
                    logger.info(f"[API REAL] Enviando para {telefone} via {api_url}")
                else:
                    # Mock: Apenas log
                    logger.info(f"[MOCK ENVIO] WhatsApp para {candidato.nome_completo} ({telefone}): {msg}")
                
                resultados['sucesso'] += 1
                
            except Exception as e:
                logger.error(f"Falha ao enviar para {candidato.nome_completo}: {e}")
                resultados['falhas'] += 1
                
        return resultados
