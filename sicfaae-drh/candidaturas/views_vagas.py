# Views para Gestão de Vagas
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
import string
import random
from django.contrib.auth.decorators import login_required
from candidaturas.models import Vaga, Candidato, EntrevistadorVaga
from candidaturas.forms import VagaForm, VagaFormEtapa1, VagaFormEtapa2, AbrirConcursoForm, CriarEntrevistadorVagaForm
from candidaturas.utils import render_to_pdf


class ListaVagasView(LoginRequiredMixin, generic.ListView):
    """Lista todas as vagas com filtros de status."""
    model = Vaga
    template_name = 'candidaturas/vagas/lista_vagas.html'
    context_object_name = 'vagas'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Vaga.objects.all().order_by('-data_criacao')
        
        # Filtro de status
        status = self.request.GET.get('status')
        if status == 'ativas':
            queryset = queryset.filter(ativa=True)
        elif status == 'inativas':
            queryset = queryset.filter(ativa=False)
        
        # Filtro de pesquisa
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search) | Q(descricao__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_atual'] = self.request.GET.get('status', 'todas')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class CriarVagaEtapa1View(LoginRequiredMixin, generic.FormView):
    """Etapa 1: Dados básicos da vaga"""
    template_name = 'candidaturas/vagas/form_vaga_etapa1.html'
    form_class = VagaFormEtapa1
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Salvar dados na sessão
        self.request.session['vaga_etapa1'] = {
            'titulo': form.cleaned_data['titulo'],
            'descricao': form.cleaned_data['descricao'],
            'data_inicio': form.cleaned_data['data_inicio'].isoformat(),
            'data_fim': form.cleaned_data['data_fim'].isoformat(),
            'ativa': form.cleaned_data['ativa'],
            'requer_formacao': form.cleaned_data['requer_formacao'],
            'nivel_aprovacao': form.cleaned_data['nivel_aprovacao'],
            'provincia_id': form.cleaned_data['provincia'].id if form.cleaned_data.get('provincia') else None,
            'distrito_id': form.cleaned_data['distrito'].id if form.cleaned_data.get('distrito') else None,
        }
        messages.success(self.request, 'Dados básicos salvos! Agora selecione os documentos necessários.')
        return redirect('candidaturas:criar_vaga_etapa2')
    
    def get_initial(self):
        # Pré-preencher se voltar da etapa 2
        dados = self.request.session.get('vaga_etapa1', {})
        if 'data_inicio' in dados:
            from datetime import date
            dados['data_inicio'] = date.fromisoformat(dados['data_inicio'])
            dados['data_fim'] = date.fromisoformat(dados['data_fim'])
            
        # Converter IDs p/ strings ou inteiros para carregamento dos ModelChoiceFields
        if dados.get('provincia_id'):
            dados['provincia'] = dados['provincia_id']
        if dados.get('distrito_id'):
            dados['distrito'] = dados['distrito_id']
            
        return dados
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Nova Vaga - Etapa 1/2'
        return context


class CriarVagaEtapa2View(LoginRequiredMixin, generic.FormView):
    """Etapa 2: Seleção de documentos necessários"""
    template_name = 'candidaturas/vagas/form_vaga_etapa2.html'
    form_class = VagaFormEtapa2
    
    def dispatch(self, request, *args, **kwargs):
        # Redirecionar para etapa 1 se não houver dados
        if 'vaga_etapa1' not in request.session:
            messages.warning(request, 'Por favor, preencha os dados básicos primeiro.')
            return redirect('candidaturas:criar_vaga_etapa1')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Passar dados da etapa 1 para exibição
        context['vaga_dados'] = self.request.session.get('vaga_etapa1', {})
        context['titulo_pagina'] = 'Nova Vaga - Etapa 2/2'
        return context
    
    def form_valid(self, form):
        from datetime import date
        
        # Recuperar dados da etapa 1
        dados_etapa1 = self.request.session.get('vaga_etapa1')
        
        # Criar vaga
        vaga = Vaga.objects.create(
            titulo=dados_etapa1['titulo'],
            descricao=dados_etapa1['descricao'],
            data_inicio=date.fromisoformat(dados_etapa1['data_inicio']),
            data_fim=date.fromisoformat(dados_etapa1['data_fim']),
            ativa=dados_etapa1['ativa'],
            requer_formacao=dados_etapa1['requer_formacao'],
            nivel_aprovacao=dados_etapa1.get('nivel_aprovacao', 'DISTRITAL'),
            provincia_id=dados_etapa1.get('provincia_id'),
            distrito_id=dados_etapa1.get('distrito_id'),
        )
        
        # Adicionar documentos necessários
        docs = []
        if form.cleaned_data.get('doc_bi'):
            docs.append('bi')
        if form.cleaned_data.get('doc_certificado'):
            docs.append('certificado')
        if form.cleaned_data.get('doc_cv'):
            docs.append('cv')
        if form.cleaned_data.get('doc_foto'):
            docs.append('foto')
        
        vaga.documentos_necessarios = docs
        vaga.save()
        
        # Limpar sessão
        del self.request.session['vaga_etapa1']
        
        messages.success(self.request, f'Vaga "{vaga.titulo}" criada com sucesso!')
        return redirect('candidaturas:lista_vagas')


class EditarVagaView(LoginRequiredMixin, generic.UpdateView):
    """Edita uma vaga existente."""
    model = Vaga
    form_class = VagaForm
    template_name = 'candidaturas/vagas/form_vaga.html'
    success_url = reverse_lazy('candidaturas:lista_vagas')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, f'Vaga "{form.instance.titulo}" atualizada com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Editar Vaga'
        context['botao_texto'] = 'Salvar Alterações'
        return context


class DetalheVagaView(LoginRequiredMixin, generic.DetailView):
    """Exibe detalhes de uma vaga com estatísticas."""
    model = Vaga
    template_name = 'candidaturas/vagas/detalhe_vaga.html'
    context_object_name = 'vaga'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vaga = self.object
        
        # Estatísticas da vaga
        context['total_candidatos'] = vaga.candidatos.count()
        context['candidatos_pendentes'] = vaga.candidatos.filter(estado=Candidato.Estado.PENDENTE).count()
        context['candidatos_docs_aprovados'] = vaga.candidatos.filter(estado=Candidato.Estado.DOCS_APROVADOS).count()
        context['candidatos_entrevista_agendada'] = vaga.candidatos.filter(estado=Candidato.Estado.ENTREVISTA_AGENDADA).count()
        context['candidatos_aprovados'] = vaga.candidatos.filter(estado=Candidato.Estado.ENTREVISTA_APROVADA).count()
        context['candidatos_enviados_defc'] = vaga.candidatos.filter(estado=Candidato.Estado.ENVIADO_DEFC).count()
        
        # Lista de candidatos recentes
        context['candidatos_recentes'] = vaga.candidatos.all().order_by('-data_criacao')[:10]
        
        # Pode Enviar Lote?
        context['pode_enviar_aprovados'] = context['candidatos_aprovados'] > 0 and vaga.requer_formacao
        
        return context

@login_required
def enviar_aprovados_vaga_formacao(request, pk):
    vaga = get_object_or_404(Vaga, pk=pk)
    
    from django.contrib import messages
    from django.utils import timezone
    
    candidatos_aprovados = Candidato.objects.filter(
        vaga=vaga,
        estado=Candidato.Estado.ENTREVISTA_APROVADA
    )
    
    total = candidatos_aprovados.count()
    
    if total > 0:
        candidatos_ids = list(candidatos_aprovados.values_list('id', flat=True))
        Candidato.objects.filter(id__in=candidatos_ids).update(
            estado=Candidato.Estado.ENVIADO_DEFC,
            enviado_defc=True,
            data_envio_defc=timezone.now()
        )
        
        # Trigger DEFC migration script automatically
        import subprocess
        import platform
        import os
        python_cmd = 'python' if platform.system() == 'Windows' else 'python3'
        defc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sicfaae-defc'))
        script_path = os.path.join(defc_dir, 'migrate_defc.py')
        
        if os.path.exists(script_path):
            try:
                subprocess.Popen([python_cmd, script_path], cwd=defc_dir)
                messages.success(request, f"Sucesso: {total} candidatos aprovados transferidos e sincronização DEFC iniciada.")
            except Exception as e:
                messages.warning(request, f"{total} candidatos marcados como enviados, mas falha ao sincronizar com DEFC: {str(e)}")
        else:
            messages.success(request, f"Sucesso: {total} candidatos aprovados transferidos para a Formação (DEFC)!")
    else:
        messages.warning(request, "Nenhum candidato aprovado na entrevista foi encontrado para transferência.")
        
    return redirect('candidaturas:detalhe_vaga', pk=vaga.pk)


def alternar_status_vaga(request, pk):
    """Ativa ou desativa uma vaga."""
    vaga = get_object_or_404(Vaga, pk=pk)
    vaga.ativa = not vaga.ativa
    vaga.save()
    
    status = "ativada" if vaga.ativa else "desativada"
    messages.success(request, f'Vaga "{vaga.titulo}" {status} com sucesso!')
    
    return redirect('candidaturas:lista_vagas')

class AbrirConcursoView(LoginRequiredMixin, generic.UpdateView):
    """View para abrir o concurso e definir número de vagas, gerando o PDF."""
    model = Vaga
    form_class = AbrirConcursoForm
    template_name = 'candidaturas/vagas/abrir_concurso.html'
    
    def get_success_url(self):
        return reverse_lazy('candidaturas:detalhe_vaga', kwargs={'pk': self.object.pk})
        
    def form_valid(self, form):
        vaga = form.save(commit=False)
        vaga.concurso_aberto = True
        
        # Gerar o PDF do concurso
        from django.template.loader import get_template
        from xhtml2pdf import pisa
        from io import BytesIO
        from candidaturas.utils import link_callback
        
        context_dict = {
            'vaga': vaga,
            'data_geracao': timezone.now(),
        }
        
        template = get_template('candidaturas/pdf/concurso_oficial.html')
        html = template.render(context_dict)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)
        
        if not pdf.err:
            pdf_name = f"Concurso_Vaga_{vaga.pk}.pdf"
            vaga.documento_concurso.save(pdf_name, ContentFile(result.getvalue()), save=False)
        else:
            messages.error(self.request, "Erro ao gerar PDF oficial.")
            
        vaga.save()
        messages.success(self.request, f"Concurso aberto com sucesso para {vaga.numero_vagas} vagas!")
        return redirect(self.get_success_url())

class ApagarVagaView(LoginRequiredMixin, generic.DeleteView):
    """View para remover uma vaga permanentemente."""
    model = Vaga
    template_name = 'candidaturas/vagas/vaga_confirm_delete.html'
    success_url = reverse_lazy('candidaturas:lista_vagas')
    
    def form_valid(self, form):
        messages.success(self.request, f'Vaga "{self.object.titulo}" apagada com sucesso!')
        return super().form_valid(form)

class AdicionarEntrevistadorVagaView(LoginRequiredMixin, generic.CreateView):
    """View para criar um entrevistador diretamente alocado a uma vaga específica."""
    model = EntrevistadorVaga
    form_class = CriarEntrevistadorVagaForm
    template_name = 'candidaturas/vagas/adicionar_entrevistador.html'
    
    def get_vaga(self):
        return get_object_or_404(Vaga, pk=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vaga'] = self.get_vaga()
        return context
        
    def get_success_url(self):
        return reverse_lazy('candidaturas:detalhe_vaga', kwargs={'pk': self.get_vaga().pk})
        
    def form_valid(self, form):
        vaga = self.get_vaga()
        entrevistador_vaga = form.save(commit=False)
        entrevistador_vaga.vaga = vaga
        
        # Gerar código de acesso (ex: ENT-A8F29)
        chars = string.ascii_uppercase + string.digits
        codigo = f"ENT-{''.join(random.choices(chars, k=5))}"
        while EntrevistadorVaga.objects.filter(codigo_acesso=codigo).exists():
            codigo = f"ENT-{''.join(random.choices(chars, k=5))}"
            
        entrevistador_vaga.codigo_acesso = codigo
        
        # Criar o utilizador Django subjacente com username e password = codigo
        # Is_staff é importante para passar no decorator @staff_member_required nalgumas áreas se necessário,
        # mas no portal do entrevistador usaremos uma view simples.
        user = User.objects.create_user(
            username=codigo,
            password=codigo,
            first_name=entrevistador_vaga.nome,
        )
        user.is_staff = True
        user.save()
        
        entrevistador_vaga.usuario = user
        entrevistador_vaga.save()
        
        messages.success(
            self.request, 
            f"Entrevistador {entrevistador_vaga.nome} registado com sucesso! O código de acesso gerado é: {codigo}. Partilhe-o com o entrevistador."
        )
        return redirect(self.get_success_url())
