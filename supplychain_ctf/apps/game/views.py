from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import render

# Create your views here.
from .models import Game, GameState, SystemState, Vendor


@login_required
def list_games(request):
    games = Game.objects.all()
    return render(request, 'game/list_games.html', {'games': games})

@login_required
def start_game(request, game_id):
    game = Game.objects.get(pk=game_id)
    game_state = game.start_new_game(request.user)
    return render(request, 'game/game_state.html', {'game_state': game_state })

@login_required
def game_state_view(request, game_state_id):
    system_queryset = SystemState.objects.select_related("system")
    game_state = GameState.objects.filter(pk=game_state_id)\
        .prefetch_related(Prefetch("systemstate_set", queryset=system_queryset))

    # security check, make sure the game exists and this is a game for THIS user, not just any user
    if game_state.count() == 0 or game_state[0].player.user != request.user:
        return HttpResponseForbidden()

    return render(request, 'game/game_state.html', {'game_state': game_state[0]})

@login_required
def procure_systemstate(request, systemstate_id, vendor_id):
    systemstate_set = SystemState.objects.filter(pk=systemstate_id).select_related("game_state__player")
    # security check, make sure the game exists and this is a game for THIS user, not just any user
    if systemstate_set.count() == 0 or systemstate_set[0].game_state.player.user != request.user:
        return HttpResponseForbidden()

    systemstate = systemstate_set[0]
    vendor = Vendor.objects.get(pk=vendor_id)
    if systemstate.procured:
        return HttpResponseForbidden("Nice try but you've already procured this one")


    systemstate.procured = True
    systemstate.chosen_vendor = vendor
    # adjust and apply the costs
    systemstate.downtime += int(systemstate.system.downtime_cost*vendor.downtime_cost_multiplier)
    systemstate.game_state.score -= int(systemstate.system.setup_cost*vendor.setup_cost_multiplier)

    # save it and return
    systemstate.save()
    systemstate.game_state.save()

    return game_state_view(request, systemstate.game_state.pk)

def home(request, ):

    return render(request, 'game/game_state.html', )