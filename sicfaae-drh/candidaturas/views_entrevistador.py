from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import EntrevistadorVaga, Candidato, Entrevista
from .forms import AvaliacaoEntrevistaForm

class LoginEntrevistadorVagaView(LoginView):
    template_name = 'candidaturas/entrevistador/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('candidaturas:painel_entrevistador_vaga')
        
    def form_invalid(self, form):
        messages.error(self.request, "Código de acesso ou nome de utilizador inválidos.")
        return super().form_invalid(form)

class PainelEntrevistadorVagaView(LoginRequiredMixin, generic.ListView):
    template_name = 'candidaturas/entrevistador/painel.html'
    context_object_name = 'candidatos'
    
    def dispatch(self, request, *args, **kwargs):
        # Guarantee that only true EntrevistadorVaga users hit this view
        if not hasattr(request.user, 'entrevistador_vaga'):
            messages.error(request, "Acesso restrito a entrevistadores de vaga.")
            from django.contrib.auth import logout
            logout(request)
            return redirect('candidaturas:login_entrevistador_vaga')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        entrevistador = self.request.user.entrevistador_vaga
        # Show candidates for their Vaga that are ready to be interviewed or already interviewed
        # Ready states: DOCS_APROVADOS, ENTREVISTA_AGENDADA. We might show all just to be safe, filter by their Vaga
        return Candidato.objects.filter(vaga=entrevistador.vaga).order_by('nome_completo')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entrevistador'] = self.request.user.entrevistador_vaga
        return context

class AvaliarCandidatoVagaView(LoginRequiredMixin, generic.UpdateView):
    model = Entrevista
    form_class = AvaliacaoEntrevistaForm
    template_name = 'candidaturas/entrevistador/avaliar.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'entrevistador_vaga'):
            messages.error(request, "Acesso restrito.")
            return redirect('candidaturas:login_entrevistador_vaga')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        candidato = get_object_or_404(Candidato, pk=self.kwargs.get('pk'))
        
        # Ensure that this candidate actually belongs to the interviewer's vaga
        if candidato.vaga != self.request.user.entrevistador_vaga.vaga:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Não pode avaliar um candidato de outra vaga.")
            
        entrevista, pv = Entrevista.objects.get_or_create(
            candidato=candidato,
            defaults={
                'data_hora': timezone.now(),
                'local': 'Online / Presencial (Vaga)',
                'entrevistador': self.request.user,
                'status': Entrevista.Status.AGENDADA
            }
        )
        return entrevista

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['candidato'] = self.object.candidato
        context['entrevistador'] = self.request.user.entrevistador_vaga
        return context
        
    def get_success_url(self):
        return reverse_lazy('candidaturas:painel_entrevistador_vaga')

    def form_valid(self, form):
        entrevista = form.save(commit=False)
        entrevista.status = Entrevista.Status.REALIZADA
        # Set the interviewer if not set
        if not entrevista.entrevistador:
            entrevista.entrevistador = self.request.user
        entrevista.save()
        
        # Atualizar Candidato status
        candidato = entrevista.candidato
        if entrevista.resultado == Entrevista.Resultado.APROVADO:
            candidato.estado = Candidato.Estado.ENTREVISTA_APROVADA
        elif entrevista.resultado == Entrevista.Resultado.REPROVADO:
            candidato.estado = Candidato.Estado.ENTREVISTA_REPROVADA
        candidato.save()
        
        messages.success(self.request, f"Avaliação de {candidato.nome_completo} guardada com sucesso!")
        return super().form_valid(form)
