from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from .models import Turma, TipoFormacao, PlanoFormacaoDistrito, Certificacao, Brigada
from .forms import TurmaForm, ConfiguracaoSistemaForm, BrigadaForm
from core.models import ConfiguracaoSistema, CandidatoFormacao
from django.db.models import Count, Q
from django.urls import reverse_lazy, reverse

class IsSTAEAdminMixin(UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_superuser:
            return True
        perfil = getattr(self.request.user, 'perfil', None)
        if perfil and perfil.nivel in ['CENTRAL', 'PROVINCIAL']:
            return True
        return False

class ConfiguracaoSistemaUpdateView(LoginRequiredMixin, IsSTAEAdminMixin, generic.UpdateView):
    model = ConfiguracaoSistema
    form_class = ConfiguracaoSistemaForm
    template_name = 'formacao/configuracoes.html'
    success_url = reverse_lazy('formacao:configuracoes')

    def get_object(self, queryset=None):
        return ConfiguracaoSistema.get_config()
        
    def form_valid(self, form):
        messages.success(self.request, "Configurações Globais atualizadas com sucesso.")
        return super().form_valid(form)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Configurações Globais"
        return context


from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Turma, TipoFormacao, PlanoFormacaoDistrito
from django.db.models import Count, Q
from django.urls import reverse_lazy
from .forms import TurmaForm

# --- Views de Listagem ---

class ListaTurmasView(LoginRequiredMixin, generic.ListView):
    model = Turma
    template_name = 'formacao/lista_turmas.html'
    context_object_name = 'turmas'
    paginate_by = 10
    ordering = ['-criada_em']
    login_url = '/accounts/login/'

    def get_queryset(self):
        qs = super().get_queryset()
        tipo = self.request.GET.get('tipo')
        concluida = self.request.GET.get('concluida')

        if tipo:
            qs = qs.filter(tipo_formacao=tipo)

        if concluida == 'sim':
            qs = qs.filter(concluida=True)
        elif concluida == 'nao':
            qs = qs.filter(concluida=False)

        # Filtragem Hierárquica
        from core.models import PerfilUtilizador
        from core.utils import obter_perfil_usuario

        perfil = obter_perfil_usuario(self.request.user)

        if self.request.user.is_superuser:
            pass
        elif perfil:
            if perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
                qs = qs.filter(
                    Q(distrito__provincia=perfil.provincia) | Q(provincia=perfil.provincia)
                )
            elif perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
                qs = qs.filter(distrito=perfil.distrito)
        else:
            qs = qs.none()

        qs = qs.select_related('distrito', 'local', 'provincia')
        qs = qs.annotate(
            total_alunos=Count('alunos', distinct=True)
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Gestão de Turmas"
        context['tipos_formacao'] = TipoFormacao.choices
        return context

class ListaTurmasFormadoresView(ListaTurmasView):
    """Todos os formadores — acessível ao STAE Central e Provincial"""
    def dispatch(self, request, *args, **kwargs):
        from core.utils import obter_perfil_usuario
        from core.models import PerfilUtilizador
        perfil = obter_perfil_usuario(request.user)
        if not request.user.is_superuser and perfil:
            if perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("Acesso restrito ao STAE Central ou Provincial.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(tipo_formacao__in=[
            TipoFormacao.FORMADORES_NACIONAIS,
            TipoFormacao.FORMADORES_PROVINCIAIS,
            TipoFormacao.FORMADORES
        ])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Turmas de Formadores"
        return context

class ListaTurmasFormadoresNacionaisView(ListaTurmasView):
    """
    Turmas de Formadores Nacionais.
    Acesso exclusivo ao STAE Central (superuser ou perfil CENTRAL).
    A Província não pode gerir formadores nacionais.
    """
    def dispatch(self, request, *args, **kwargs):
        from django.core.exceptions import PermissionDenied
        from core.utils import obter_perfil_usuario
        from core.models import PerfilUtilizador
        if not request.user.is_superuser:
            perfil = obter_perfil_usuario(request.user)
            if not perfil or perfil.nivel not in [
                PerfilUtilizador.Nivel.CENTRAL,
            ]:
                raise PermissionDenied(
                    "Esta secção é exclusiva do STAE Central. "
                    "A formação de Formadores Nacionais é gerida pela sede."
                )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(tipo_formacao=TipoFormacao.FORMADORES_NACIONAIS)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Formadores Nacionais (Direções Provinciais)"
        return context

class ListaTurmasFormadoresProvinciaisView(ListaTurmasView):
    """
    Turmas de Formadores Provinciais.
    Acesso ao STAE Central e STAE Provincial (não ao Distrital).
    """
    def dispatch(self, request, *args, **kwargs):
        from django.core.exceptions import PermissionDenied
        from core.utils import obter_perfil_usuario
        from core.models import PerfilUtilizador
        if not request.user.is_superuser:
            perfil = obter_perfil_usuario(request.user)
            if not perfil or perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
                raise PermissionDenied(
                    "Esta secção não está disponível para o nível Distrital."
                )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(tipo_formacao=TipoFormacao.FORMADORES_PROVINCIAIS)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Formadores Provinciais"
        return context

class ListaTurmasMMVView(ListaTurmasView):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(tipo_formacao=TipoFormacao.MMV)

class ListaTurmasAgentesEducacaoView(ListaTurmasView):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(tipo_formacao=TipoFormacao.AGENTES_EDUCACAO)

class ListaTurmasBrigadistasView(ListaTurmasView):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(tipo_formacao=TipoFormacao.BRIGADISTAS)


# --- Views Stub / Placeholder (Restauradas) ---

class GerarTurmasFormadoresView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'formacao/gerar_turmas.html'

from .forms import TurmaForm

class CriarTurmaView(LoginRequiredMixin, generic.CreateView):
    template_name = 'formacao/form_turma.html'
    form_class = TurmaForm
    success_url = reverse_lazy('formacao:lista_turmas')

    def get_initial(self):
        initial = super().get_initial()
        # Pré-preencher com base na query string (ex: ?tipo=BRIGADISTAS)
        tipo = self.request.GET.get('tipo')
        if tipo:
            initial['tipo_formacao'] = tipo
        if tipo:
            initial['tipo_formacao'] = tipo
        return initial

    def form_invalid(self, form):
        print("❌ Erros do formulário:", form.errors)
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Local
        context['locais_disponiveis'] = Local.objects.values_list('nome', flat=True).distinct()
        return context

class DetalheTurmaView(LoginRequiredMixin, generic.DetailView):
    model = Turma
    template_name = 'formacao/detalhe_turma.html'
    context_object_name = 'turma'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        turma = self.object
        context['alunos'] = turma.alunos.all()
        
        # Obter candidatos já matriculados para os excluir da lista de disponíveis
        alunos_ids = turma.alunos.values_list('id', flat=True)
        
        from core.models import CandidatoFormacao
        qs = CandidatoFormacao.objects.filter(ativo=True).exclude(id__in=alunos_ids)
        
        if turma.tipo_formacao in [TipoFormacao.FORMADORES_NACIONAIS, TipoFormacao.FORMADORES_PROVINCIAIS]:
            qs = qs.filter(tipo_agente=CandidatoFormacao.TipoAgente.FORMADOR)
            # Para provinciais, restringir à província
            if turma.provincia:
                qs = qs.filter(provincia=turma.provincia)
            elif turma.distrito:
                qs = qs.filter(provincia=turma.distrito.provincia)
        elif turma.tipo_formacao == TipoFormacao.MMV:
            qs = qs.filter(tipo_agente=CandidatoFormacao.TipoAgente.MMV, distrito=turma.distrito)
        elif turma.tipo_formacao == TipoFormacao.BRIGADISTAS:
            qs = qs.filter(tipo_agente=CandidatoFormacao.TipoAgente.BRIGADISTA, distrito=turma.distrito)
        elif turma.tipo_formacao == TipoFormacao.AGENTES_EDUCACAO:
            qs = qs.filter(tipo_agente=CandidatoFormacao.TipoAgente.AGENTE_CIVICO, distrito=turma.distrito)
            
        context['candidatos_disponiveis'] = qs.order_by('nome_completo')
        return context

    def post(self, request, *args, **kwargs):
        turma = self.get_object()
        
        # Remover aluno
        remover_id = request.POST.get('remover_aluno_id')
        if remover_id:
            from core.models import CandidatoFormacao
            try:
                aluno = CandidatoFormacao.objects.get(id=remover_id)
                turma.alunos.remove(aluno)
                messages.success(request, f"O aluno {aluno.nome_completo} foi removido da turma com sucesso.")
            except CandidatoFormacao.DoesNotExist:
                messages.error(request, "Aluno não encontrado.")
            return redirect('formacao:detalhe_turma', pk=turma.pk)
            
        # Adicionar alunos
        candidatos_ids = request.POST.getlist('candidatos_ids')
        if candidatos_ids:
            from core.models import CandidatoFormacao
            candidatos = CandidatoFormacao.objects.filter(id__in=candidatos_ids)
            for c in candidatos:
                turma.alunos.add(c)
            messages.success(request, f"{candidatos.count()} aluno(s) adicionado(s) à turma com sucesso.")
        else:
            messages.warning(request, "Nenhum aluno selecionado para adicionar.")
            
        return redirect('formacao:detalhe_turma', pk=turma.pk)

class EditarTurmaView(LoginRequiredMixin, generic.UpdateView):
    model = Turma
    template_name = 'formacao/form_turma.html'
    form_class = TurmaForm
    success_url = reverse_lazy('formacao:lista_turmas')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Local
        context['locais_disponiveis'] = Local.objects.values_list('nome', flat=True).distinct()
        return context

class ApagarTurmaView(LoginRequiredMixin, generic.DeleteView):
    model = Turma
    template_name = 'formacao/confirmar_apagar_turma.html'
    success_url = reverse_lazy('formacao:lista_turmas')

from formacao.models import Certificacao

class LancarNotasTurmaView(LoginRequiredMixin, generic.View):
    template_name = 'formacao/lancar_notas.html'
    
    def get(self, request, pk, *args, **kwargs):
        turma = get_object_or_404(Turma, pk=pk)
        alunos = turma.alunos.all()
        # Buscar certificações existentes para preencher form
        certificacoes = Certificacao.objects.filter(turma=turma).select_related('candidato')
        notas_map = {cert.candidato_id: cert for cert in certificacoes}
        
        alunos_data = []
        for aluno in alunos:
            cert = notas_map.get(aluno.id)
            alunos_data.append({
                'aluno': aluno,
                'nota_final': cert.nota_final if cert else '',
                'percentual_presenca': cert.percentual_presenca if cert else 0,
                'cert_id': cert.id if cert else ''
            })
            
        context = {
            'turma': turma,
            'alunos_data': alunos_data,
            'titulo_pagina': f"Lançamento de Notas - {turma.nome}"
        }
        return render(request, self.template_name, context)

    def post(self, request, pk, *args, **kwargs):
        turma = get_object_or_404(Turma, pk=pk)
        
        for key, value in request.POST.items():
            if key.startswith('nota_'):
                try:
                    aluno_id = int(key.replace('nota_', ''))
                    nota = float(value.replace(',', '.')) if value.strip() else None
                    if nota is not None and (nota < 0 or nota > 20):
                        messages.warning(request, f"Nota inválida para o aluno ID {aluno_id}. Deve estar entre 0 e 20.")
                        continue
                    
                    presenca_str = request.POST.get(f'presenca_{aluno_id}', '0')
                    presenca = float(presenca_str.replace(',', '.')) if presenca_str.strip() else 0
                    
                    # Usa get_or_create para garantir que não duplica
                    cert, created = Certificacao.objects.get_or_create(
                         turma=turma,
                         candidato_id=aluno_id,
                         defaults={
                             'tipo': turma.tipo_formacao,
                             'percentual_presenca': presenca,
                             'nota_final': nota
                         }
                    )
                    
                    if not created:
                        cert.nota_final = nota
                        cert.percentual_presenca = presenca
                        # Não gera novamente o número se já existir a não ser que falte
                        if not cert.numero_certificado:
                             cert.gerar_numero_certificado()
                        cert.save()
                        
                except ValueError:
                    pass # Ignorar valores não numéricos
        
        # Iniciar thread em background para gerar as certificações automaticamente
        t = threading.Thread(target=gerar_pdfs_background, args=(turma.pk,))
        t.daemon = True
        t.start()
        
        from django.contrib import messages
        messages.success(request, "Notas gravadas com sucesso.")
        messages.info(request, "A geração das certificações (PDF) foi iniciada em segundo plano.")
        return redirect('formacao:detalhe_turma', pk=turma.pk)

import openpyxl
from django.http import HttpResponse

class ExportarTurmaExcelView(LoginRequiredMixin, generic.View):
    def get(self, request, pk, *args, **kwargs):
        turma = get_object_or_404(Turma, pk=pk)
        alunos = turma.alunos.all()
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=turma_{turma.numero}_{turma.distrito.nome}.xlsx'
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Turma {turma.numero}"
        
        ws.append(['Nome Completo', 'BI', 'Género', 'Telefone', 'Distrito'])
        for aluno in alunos:
            ws.append([
                aluno.nome_completo,
                aluno.numero_bi,
                aluno.get_genero_display(),
                aluno.numero_telefone,
                aluno.distrito.nome
            ])
            
        wb.save(response)
        return response

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class ExportarTurmaPDFView(LoginRequiredMixin, generic.View):
    def get(self, request, pk, *args, **kwargs):
        turma = get_object_or_404(Turma, pk=pk)
        alunos = turma.alunos.all()
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=pauta_turma_{turma.numero}.pdf'
        
        doc = SimpleDocTemplate(response, pagesize=landscape(A4))
        elements = []
        styles = getSampleStyleSheet()
        
        elements.append(Paragraph(f"Pauta da Turma: {turma.nome}", styles['Title']))
        local_nome = turma.local.nome if turma.local else 'N/A'
        elements.append(Paragraph(f"Distrito: {turma.distrito.nome} | Local: {local_nome}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        data = [['Nome Completo', 'BI', 'Género', 'Telefone', 'Assinatura']]
        for aluno in alunos:
            data.append([aluno.nome_completo, aluno.numero_bi, aluno.get_genero_display(), aluno.numero_telefone, ''])
            
        t = Table(data, colWidths=[200, 100, 60, 100, 200])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        
        elements.append(t)
        doc.build(elements)
        
        return response

class GerarTurmasView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'formacao/gerar_turmas.html'


import threading
import time
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.core.files.base import ContentFile

def gerar_pdfs_background(turma_id):
    # Aguarda um pequeno momento para a transacção do request terminar
    time.sleep(2)
    turma = Turma.objects.get(pk=turma_id)
    certificacoes = Certificacao.objects.filter(turma=turma, documento_pdf='')
    
    for cert in certificacoes:
        try:
            # Geração muito básica de PDF apenas como placeholder simulando I/O pesado
            from io import BytesIO
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
            styles = getSampleStyleSheet()
            elements = []
            elements.append(Paragraph(f"Certificado de {cert.get_tipo_display()}", styles['Title']))
            elements.append(Spacer(1, 40))
            elements.append(Paragraph(f"Certifica-se que {cert.candidato.nome_completo}", styles['Title']))
            elements.append(Spacer(1, 20))
            elements.append(Paragraph(f"Concluiu com sucesso a formação. Nota: {cert.nota_final} Valores", styles['Normal']))
            doc.build(elements)
            
            pdf_data = buffer.getvalue()
            buffer.close()
            
            # Anexar ao model (.save() dentro da thread)
            nome_arquivo = f"certificado_{cert.numero_certificado}.pdf"
            cert.documento_pdf.save(nome_arquivo, ContentFile(pdf_data), save=True)
            
            # TODO: Simular envio de e-mail/SMS aqui
            
        except Exception as e:
            print(f"Erro ao gerar PDF para a certificacao {cert.id}: {e}")

class ProcessarCertificacoesView(LoginRequiredMixin, generic.View):
    def post(self, request, pk, *args, **kwargs):
        turma = get_object_or_404(Turma, pk=pk)
        
        # Iniciar thread em background para não bloquear o utilizador
        t = threading.Thread(target=gerar_pdfs_background, args=(turma.pk,))
        t.daemon = True
        t.start()
        
        messages.info(request, "A geração dos PDFs começou em segundo plano. Poderá consultar os ficheiros na página de Certificações dentro de alguns minutos.")
        return redirect('formacao:detalhe_turma', pk=turma.pk)

class ListaCertificacoesView(LoginRequiredMixin, generic.ListView):
    model = Certificacao
    template_name = 'formacao/lista_certificacoes.html'
    context_object_name = 'certificacoes'
    paginate_by = 20
    
    def get_queryset(self):
        from core.utils import obter_perfil_usuario
        from core.models import PerfilUtilizador
        from django.db.models import Q
        
        perfil = obter_perfil_usuario(self.request.user)
        qs = Certificacao.objects.select_related('candidato', 'turma', 'turma__distrito')
        
        # Filtros Hierárquicos
        if not self.request.user.is_superuser:
            if perfil:
                if perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
                    qs = qs.filter(turma__distrito__provincia=perfil.provincia)
                elif perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
                    qs = qs.filter(turma__distrito=perfil.distrito)
        
        # Filtros de busca
        tipo = self.request.GET.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
            
        estado = self.request.GET.get('estado')
        if estado:
            qs = qs.filter(estado=estado)
            
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(candidato__nome_completo__icontains=search) | 
                Q(candidato__codigo_candidato__icontains=search) |
                Q(numero_certificado__icontains=search)
            )
            
        return qs.order_by('-criada_em')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos'] = Certificacao.TipoCertificacao.choices
        context['estados'] = Certificacao.EstadoCertificacao.choices
        return context

# --- Views para Gestão de Brigadas ---

class BrigadaListView(LoginRequiredMixin, generic.ListView):
    model = Brigada
    template_name = 'formacao/lista_brigadas.html'
    context_object_name = 'brigadas'
    paginate_by = 15

    def get_queryset(self):
        from core.utils import obter_perfil_usuario
        from core.models import PerfilUtilizador
        perfil = obter_perfil_usuario(self.request.user)
        qs = Brigada.objects.select_related('distrito').prefetch_related('membros')
        
        if not self.request.user.is_superuser:
            if perfil:
                if perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
                    qs = qs.filter(distrito__provincia=perfil.provincia)
                elif perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
                    qs = qs.filter(distrito=perfil.distrito)
        return qs

class BrigadaCreateView(LoginRequiredMixin, generic.CreateView):
    model = Brigada
    form_class = BrigadaForm
    template_name = 'formacao/form_brigada.html'
    success_url = reverse_lazy('formacao:lista_brigadas')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Brigada criada com sucesso.")
        return super().form_valid(form)

class BrigadaUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Brigada
    form_class = BrigadaForm
    template_name = 'formacao/form_brigada.html'
    success_url = reverse_lazy('formacao:lista_brigadas')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Brigada atualizada com sucesso.")
        return super().form_valid(form)

class BrigadaDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Brigada
    template_name = 'formacao/confirmar_apagar_brigada.html'
    success_url = reverse_lazy('formacao:lista_brigadas')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Brigada removida com sucesso.")
        return super().delete(request, *args, **kwargs)

from django.http import JsonResponse
class ObterBrigadistasDisponiveisView(LoginRequiredMixin, generic.View):
    """
    Retorna JSON com os brigadistas certificados disponíveis num distrito.
    Usado para atualizar dinamicamente o formulário de Brigada.
    """
    def get(self, request, *args, **kwargs):
        distrito_id = request.GET.get('distrito_id')
        if not distrito_id:
            return JsonResponse({'status': 'error', 'message': 'Distrito não fornecido'}, status=400)
        
        # Apenas candidatos com certificação ativa de BRIGADISTA no distrito
        certificados = Certificacao.objects.filter(
            tipo=Certificacao.TipoCertificacao.BRIGADISTA,
            estado=Certificacao.EstadoCertificacao.ATIVO,
            turma__distrito_id=distrito_id
        ).select_related('candidato')
        
        data = [
            {
                'id': cert.candidato.id,
                'nome': cert.candidato.nome_completo,
                'codigo': cert.candidato.codigo_candidato
            } for cert in certificados
        ]
        
        return JsonResponse({'status': 'success', 'data': data})

class DashboardGeralView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'formacao/dashboard_geral.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import CandidatoFormacao, PerfilUtilizador
        from core.utils import obter_perfil_usuario
        
        # Filtragem Hierárquica
        qs = CandidatoFormacao.objects.all()
        perfil = obter_perfil_usuario(self.request.user)
        
        if self.request.user.is_superuser:
            pass # Vê tudo
        elif perfil:
            if perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
                qs = qs.filter(provincia=perfil.provincia)
            elif perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
                qs = qs.filter(distrito=perfil.distrito)
            # CENTRAL vê tudo
        else:
            # Sem perfil e não é superuser -> não vê nada
            qs = qs.none()

        # Totais Gerais (Baseados no QuerySet Filtrado)
        context['total_formandos'] = qs.count()
        context['total_ativos'] = qs.filter(ativo=True).count()
        
        # Totais por Tipo
        context['total_mmv'] = qs.filter(tipo_agente=CandidatoFormacao.TipoAgente.MMV).count()
        context['total_civicos'] = qs.filter(tipo_agente=CandidatoFormacao.TipoAgente.AGENTE_CIVICO).count()
        context['total_brigadistas'] = qs.filter(tipo_agente=CandidatoFormacao.TipoAgente.BRIGADISTA).count()
        context['total_formadores'] = qs.filter(tipo_agente=CandidatoFormacao.TipoAgente.FORMADOR).count()
        
        # Lista Recente
        context['formandos_recentes'] = qs.order_by('-data_recepcao')[:10]
        
        return context

class RegistarFormadorView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'formacao/registar_formador.html'


# --- Views de Plano de Formação por Distrito ---

from .forms import PlanoFormacaoDistritoForm
from core.models import Distrito as DistritoModel

class PlanoFormacaoDistritoListView(LoginRequiredMixin, generic.ListView):
    """Lista todos os distritos com o seu plano de formação e cálculos automáticos"""
    model = PlanoFormacaoDistrito
    template_name = 'formacao/plano_formacao_provincia.html'
    context_object_name = 'planos'

    def get_queryset(self):
        from core.utils import obter_perfil_usuario
        from core.models import PerfilUtilizador
        perfil = obter_perfil_usuario(self.request.user)
        qs = PlanoFormacaoDistrito.objects.select_related('distrito', 'distrito__provincia')
        if self.request.user.is_superuser:
            return qs
        elif perfil and perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL and perfil.provincia:
            return qs.filter(distrito__provincia=perfil.provincia)
        elif perfil and perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL and perfil.distrito:
            return qs.filter(distrito=perfil.distrito)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.utils import obter_perfil_usuario
        from core.models import PerfilUtilizador
        perfil = obter_perfil_usuario(self.request.user)

        todos_distritos = DistritoModel.objects.select_related('provincia')
        if perfil and not self.request.user.is_superuser:
            if perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL and perfil.provincia:
                todos_distritos = todos_distritos.filter(provincia=perfil.provincia)
            elif perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL and perfil.distrito:
                todos_distritos = todos_distritos.filter(pk=perfil.distrito.pk)

        # Agrupar por província
        provincias_data = {}
        for plano in self.get_queryset():
            prov_id = plano.distrito.provincia.id
            if prov_id not in provincias_data:
                provincias_data[prov_id] = {
                    'provincia': plano.distrito.provincia,
                    'planos': [],
                    'pendentes': [],
                    'todos_submetidos': True,
                    'tem_planos_criados': False
                }
            provincias_data[prov_id]['planos'].append(plano)
            provincias_data[prov_id]['tem_planos_criados'] = True
            if plano.estado != PlanoFormacaoDistrito.EstadoPlano.SUBMETIDO_RH:
                provincias_data[prov_id]['todos_submetidos'] = False

        from core.models import ConfiguracaoSistema
        config = ConfiguracaoSistema.get_config()
        
        tipos_todos = []
        for t in PlanoFormacaoDistrito.TipoPlano.choices:
            tipo = t[0]
            if config.periodo_ativo == ConfiguracaoSistema.PeriodoEleitoral.RECENSEAMENTO and tipo == PlanoFormacaoDistrito.TipoPlano.MMV:
                continue
            if config.periodo_ativo == ConfiguracaoSistema.PeriodoEleitoral.VOTACAO and tipo == PlanoFormacaoDistrito.TipoPlano.BRIGADISTAS:
                continue
            tipos_todos.append(tipo)
            
        context['configuracao_sistema'] = config
        planos_existentes = set(
            self.get_queryset().values_list('distrito_id', 'tipo')
        )
        for d in todos_distritos:
            prov_id = d.provincia.id
            if prov_id not in provincias_data:
                provincias_data[prov_id] = {
                    'provincia': d.provincia,
                    'planos': [],
                    'pendentes': [],
                    'todos_submetidos': True,
                    'tem_planos_criados': False
                }
            for tipo in tipos_todos:
                if (d.pk, tipo) not in planos_existentes:
                    provincias_data[prov_id]['pendentes'].append({
                        'distrito': d,
                        'tipo': tipo,
                        'tipo_label': dict(PlanoFormacaoDistrito.TipoPlano.choices).get(tipo, tipo)
                    })
                    # Se há pendentes, não pode estar tudo submetido
                    provincias_data[prov_id]['todos_submetidos'] = False

        # Ordenar províncias alfabeticamente
        context['provincias_data'] = sorted(provincias_data.values(), key=lambda x: x['provincia'].nome)
        context['titulo_pagina'] = "Plano de Formação por Província e Distrito"
        return context

class SubmeterPlanosProvinciaView(LoginRequiredMixin, generic.View):
    """Submete todos os planos de uma Província (muda de Rascunho para Submetido_RH)"""
    def post(self, request, provincia_id, *args, **kwargs):
        from django.contrib import messages
        from django.shortcuts import redirect
        
        planos = PlanoFormacaoDistrito.objects.filter(
            distrito__provincia_id=provincia_id, 
            estado=PlanoFormacaoDistrito.EstadoPlano.RASCUNHO
        )
        
        count = planos.update(estado=PlanoFormacaoDistrito.EstadoPlano.SUBMETIDO_RH)
        
        if count > 0:
            messages.success(request, f"{count} plano(s) da província foram submetido(s) com sucesso aos RH.")
        else:
            messages.warning(request, "Nenhum plano em rascunho encontrado para submeter.")
            
        return redirect('formacao:plano_lista')


class PlanoFormacaoDistritoUpdateView(LoginRequiredMixin, generic.UpdateView):
    """Editar plano de formação existente"""
    model = PlanoFormacaoDistrito
    form_class = PlanoFormacaoDistritoForm
    template_name = 'formacao/form_plano_distrito.html'
    success_url = reverse_lazy('formacao:plano_lista')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, "Plano de formação guardado com sucesso.")
        return super().form_valid(form)


class PlanoFormacaoDistritoCreateView(LoginRequiredMixin, generic.CreateView):
    """Criar plano de formação para um novo distrito/tipo"""
    model = PlanoFormacaoDistrito
    form_class = PlanoFormacaoDistritoForm
    template_name = 'formacao/form_plano_distrito.html'
    success_url = reverse_lazy('formacao:plano_lista')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Suporte a ?distrito=PK&tipo=BRIGADISTAS na URL
        distrito_pk = self.request.GET.get('distrito') or self.kwargs.get('distrito_pk')
        tipo = self.request.GET.get('tipo')
        if distrito_pk:
            initial['distrito'] = get_object_or_404(DistritoModel, pk=distrito_pk)
        if tipo:
            initial['tipo'] = tipo
        return initial

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, "Plano de formação criado com sucesso.")
        return super().form_valid(form)


from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .forms import FormularioCriacaoUsuario
from core.models import PerfilUtilizador
from core.utils import obter_perfil_usuario, obter_exibicao_nivel_usuario

class GerirUtilizadoresView(LoginRequiredMixin, generic.CreateView):
    template_name = 'formacao/gestao_utilizadores.html'
    form_class = FormularioCriacaoUsuario
    success_url = reverse_lazy('formacao:gestao_utilizadores')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        perfil = obter_perfil_usuario(self.request.user)
        if not request.user.is_superuser:
            pass
            # if not perfil:
            #     raise PermissionDenied("Não tem permissão para gerir utilizadores.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perfil = obter_perfil_usuario(self.request.user)
        
        if self.request.user.is_superuser or (perfil and perfil.nivel == PerfilUtilizador.Nivel.CENTRAL):
             if self.request.user.is_superuser:
                 context['lista_usuarios'] = PerfilUtilizador.objects.filter(
                     Q(nivel=PerfilUtilizador.Nivel.PROVINCIAL) | Q(nivel=PerfilUtilizador.Nivel.CENTRAL)
                 ).select_related('usuario', 'provincia')
             else:
                 context['lista_usuarios'] = PerfilUtilizador.objects.filter(nivel=PerfilUtilizador.Nivel.PROVINCIAL).select_related('usuario', 'provincia')
             context['titulo_pagina'] = "Gestão de Utilizadores Provinciais"
        elif perfil and perfil.nivel == PerfilUtilizador.Nivel.PROVINCIAL:
             context['lista_usuarios'] = PerfilUtilizador.objects.filter(
                 nivel=PerfilUtilizador.Nivel.DISTRITAL, 
                 provincia=perfil.provincia
             ).select_related('usuario', 'distrito')
             context['titulo_pagina'] = f"Gestão de Utilizadores Distritais - {perfil.provincia.nome}"
        elif perfil and perfil.nivel == PerfilUtilizador.Nivel.DISTRITAL:
             context['lista_usuarios'] = PerfilUtilizador.objects.filter(
                 distrito=perfil.distrito
             ).exclude(usuario=self.request.user).select_related('usuario', 'distrito')
             context['titulo_pagina'] = f"Gestão de Utilizadores - {perfil.distrito.nome}"
             
        context['nivel_usuario'] = obter_exibicao_nivel_usuario(self.request.user)
        # Mostrar senha gerada apenas uma vez (depois de criar um utilizador)
        context['senha_gerada'] = self.request.session.pop('senha_gerada', None)
        context['username_criado'] = self.request.session.pop('username_criado', None)
        return context
        
    def form_valid(self, form):
        import secrets
        import string
        # Gerar senha forte: 12 caracteres com letras, números e especiais
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        # Garantir pelo menos 1 de cada categoria
        password = (
            secrets.choice(string.ascii_uppercase) +
            secrets.choice(string.ascii_lowercase) +
            secrets.choice(string.digits) +
            secrets.choice("!@#$%^&*") +
            ''.join(secrets.choice(alphabet) for _ in range(8))
        )
        # Baralhar os caracteres para não ter padrão fixo no início
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        password = ''.join(password_list)

        form.save(generated_password=password)
        # Guardar na sessão para exibir no template
        self.request.session['senha_gerada'] = password
        self.request.session['username_criado'] = form.cleaned_data['username']
        messages.success(self.request, f"Utilizador '{form.cleaned_data['username']}' criado com sucesso.")
        return redirect(self.success_url)


class ResetarSenhaUtilizadorView(LoginRequiredMixin, generic.View):
    """Gera uma nova senha aleatória para o utilizador e activa deve_alterar_senha."""

    def post(self, request, pk, *args, **kwargs):
        from django.contrib.auth.models import User
        import secrets, string

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            messages.error(request, "Utilizador não encontrado.")
            return redirect('formacao:gestao_utilizadores')

        # Gerar nova senha forte
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = (
            secrets.choice(string.ascii_uppercase) +
            secrets.choice(string.ascii_lowercase) +
            secrets.choice(string.digits) +
            secrets.choice("!@#$%^&*") +
            ''.join(secrets.choice(alphabet) for _ in range(8))
        )
        pwd_list = list(pwd)
        secrets.SystemRandom().shuffle(pwd_list)
        pwd = ''.join(pwd_list)

        user.set_password(pwd)
        user.save()

        # Activar flag de obrigação de alteração
        try:
            perfil = user.perfil
            perfil.deve_alterar_senha = True
            perfil.save(update_fields=['deve_alterar_senha'])
        except Exception:
            pass

        # Guardar na sessão para exibir no modal
        request.session['senha_gerada'] = pwd
        request.session['username_criado'] = user.username
        messages.success(request, f"Senha de '{user.username}' foi resetada com sucesso.")
        return redirect('formacao:gestao_utilizadores')

class ListaLocaisView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'formacao/lista_locais.html'

class CriarLocalView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'formacao/form_local.html'

class EditarLocalView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'formacao/form_local.html'

from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    """
    Logout customizado para aceitar GET (necessário para alguns links legados ou cache).
    """
    logout(request)
    return redirect('login')

from .forms import CadastrarFormadorNacionalForm
from core.models import CandidatoFormacao

class CadastrarFormadorNacionalView(LoginRequiredMixin, IsSTAEAdminMixin, generic.CreateView):
    """
    View dedicada para as Direcções (Central ou Provinciais)
    poderem cadastrar diretamente na base de dados indivíduos que
    servirão de Formadores nas turmas de Nível 1.
    """
    model = CandidatoFormacao
    form_class = CadastrarFormadorNacionalForm
    template_name = 'formacao/cadastrar_formador.html'
    success_url = reverse_lazy('formacao:lista_turmas_formadores_nacionais')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Cadastrar Formador de Nível 1"
        
        # Gerar JSON para carregar os distritos na view com JavaScript
        import json
        from core.models import Distrito
        distritos_dict = {}
        for d in Distrito.objects.all():
            if d.provincia_id not in distritos_dict:
                distritos_dict[d.provincia_id] = []
            distritos_dict[d.provincia_id].append({'id': d.id, 'nome': d.nome})
            
        context['distritos_json'] = json.dumps(distritos_dict)
        return context

    def form_valid(self, form):
        formador = form.save(commit=False)
        
        # Forçar o Tipo de Agente a FORMADOR
        formador.tipo_agente = CandidatoFormacao.TipoAgente.FORMADOR
        
        # O Sistema Original DRH define o ID Numérico rigoroso. No DEFC é inserção "Adhoc"
        # Precisamos gerar identificadores únicos para não falhar a base de dados
        import random
        from django.db.models import Max
        
        # ID seguro DRH
        max_id = CandidatoFormacao.objects.aggregate(Max('id_drh'))['id_drh__max'] or 900000
        formador.id_drh = max_id + random.randint(1, 100)
        
        # Código descritivo seguro
        codigo = f"F1-{random.randint(1000, 9999)}"
        while CandidatoFormacao.objects.filter(codigo_candidato=codigo).exists():
            codigo = f"F1-{random.randint(1000, 9999)}"
        formador.codigo_candidato = codigo
        
        formador.save()
        messages.success(self.request, f"O formador {formador.nome_completo} foi registado com sucesso no sistema (Cód: {formador.codigo_candidato}).")
        return super().form_valid(form)

class ListaFormadoresNacionaisCRUDView(LoginRequiredMixin, generic.ListView):
    model = CandidatoFormacao
    template_name = 'formacao/lista_formadores_nacionais_crud.html'
    context_object_name = 'formadores'
    
    def get_queryset(self):
        return CandidatoFormacao.objects.filter(
            tipo_agente=CandidatoFormacao.TipoAgente.FORMADOR,
            codigo_candidato__startswith='F1-'
        ).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Formadores de Nível 1"
        return context

class EditarFormadorNacionalView(LoginRequiredMixin, IsSTAEAdminMixin, generic.UpdateView):
    model = CandidatoFormacao
    form_class = CadastrarFormadorNacionalForm
    template_name = 'formacao/cadastrar_formador.html'
    success_url = reverse_lazy('formacao:lista_formadores_nacionais_crud')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Editar Formador de Nível 1"
        
        import json
        from core.models import Distrito
        distritos_dict = {}
        for d in Distrito.objects.all():
            if d.provincia_id not in distritos_dict:
                distritos_dict[d.provincia_id] = []
            distritos_dict[d.provincia_id].append({'id': d.id, 'nome': d.nome})
            
        context['distritos_json'] = json.dumps(distritos_dict)
        return context

    def form_valid(self, form):
        formador = form.save()
        messages.success(self.request, f"O formador {formador.nome_completo} foi atualizado com sucesso.")
        return super().form_valid(form)

class ApagarFormadorNacionalView(LoginRequiredMixin, IsSTAEAdminMixin, generic.DeleteView):
    model = CandidatoFormacao
    template_name = 'formacao/confirmar_apagar_formador_nacional.html'
    success_url = reverse_lazy('formacao:lista_formadores_nacionais_crud')
    
    def delete(self, request, *args, **kwargs):
        formador = self.get_object()
        messages.success(request, f"O formador {formador.nome_completo} foi removido.")
        return super().delete(request, *args, **kwargs)

from django.http import JsonResponse
from django.db.models import F

class ObterFormadoresDisponiveisView(LoginRequiredMixin, generic.View):
    """
    Endpoint AJAX para o Select2.
    Recebe '?tipo=' com o tipo da turma que está a ser criada, e retorna 
    os formadores válidos de acordo com a Hierarquia e Aproveitamento.
    """
    def get(self, request, *args, **kwargs):
        tipo = request.GET.get('tipo', '')
        
        if not tipo:
            return JsonResponse({'results': []})
            
        if tipo in [TipoFormacao.BRIGADISTAS, TipoFormacao.MMV, TipoFormacao.AGENTES_EDUCACAO]:
            qs = CandidatoFormacao.objects.filter(
                ativo=True,
                certificacoes__turma__tipo_formacao=TipoFormacao.FORMADORES_PROVINCIAIS,
                certificacoes__nota_final__gte=F('certificacoes__turma__nota_minima_aprovacao'),
                certificacoes__percentual_presenca__gte=F('certificacoes__turma__percentual_presenca_minimo')
            ).distinct()
            
        elif tipo == TipoFormacao.FORMADORES_PROVINCIAIS:
            qs = CandidatoFormacao.objects.filter(
                ativo=True,
                certificacoes__turma__tipo_formacao=TipoFormacao.FORMADORES_NACIONAIS,
                certificacoes__nota_final__gte=F('certificacoes__turma__nota_minima_aprovacao'),
                certificacoes__percentual_presenca__gte=F('certificacoes__turma__percentual_presenca_minimo')
            ).distinct()
            
        elif tipo == TipoFormacao.FORMADORES_NACIONAIS:
            qs = CandidatoFormacao.objects.filter(
                ativo=True,
                tipo_agente=CandidatoFormacao.TipoAgente.FORMADOR,
                codigo_candidato__startswith='F1-'
            ).distinct()
            
        else:
            qs = CandidatoFormacao.objects.none()
            
        results = [
            {'id': f.id, 'text': f"{f.nome_completo} ({f.numero_bi})"}
            for f in qs
        ]
        
        return JsonResponse({'results': results})


class AlterarSenhaObrigatoriaView(LoginRequiredMixin, generic.View):
    """
    Vista que força o utilizador a definir uma nova senha pessoal.
    É activada quando deve_alterar_senha=True no perfil.
    """
    template_name = 'formacao/alterar_senha_obrigatoria.html'

    def get(self, request, *args, **kwargs):
        # Se o utilizador já não precisa alterar, redirecionar para início
        try:
            if not request.user.perfil.deve_alterar_senha:
                return redirect('formacao:lista_turmas')
        except Exception:
            pass
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        nova_senha = request.POST.get('nova_senha', '').strip()
        confirmar_senha = request.POST.get('confirmar_senha', '').strip()

        erros = []

        if len(nova_senha) < 8:
            erros.append("A senha deve ter pelo menos 8 caracteres.")
        if nova_senha != confirmar_senha:
            erros.append("As senhas não coincidem.")

        if erros:
            return render(request, self.template_name, {'erros': erros})

        # Guardar nova senha e desactivar a flag
        request.user.set_password(nova_senha)
        request.user.save()

        try:
            perfil = request.user.perfil
            perfil.deve_alterar_senha = False
            perfil.save(update_fields=['deve_alterar_senha'])
        except Exception:
            pass

        # Reautenticar para não perder a sessão
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)

        messages.success(request, "Senha alterada com sucesso! Bem-vindo ao sistema.")
        return redirect('formacao:lista_turmas')
