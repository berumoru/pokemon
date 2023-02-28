def visualize_state(state, phase, target):
    """行動選択時"""
    if phase == f'phase__set_action':
        print('-----全体-----')
        all_info = state['all_info']
        print('天候:', all_info['weather'])
        print()

        for target in ['A', 'B']:
            print(f'-----プレイヤー{target}-----')
            player = state[f'{target}_info']
            active_pokemon_id = player['active_pokemon_id']
            pokemons = player['pokemons']
            active_pokemon = pokemons[active_pokemon_id]
            waiting_num = len([k for k in range(3) if not k==active_pokemon_id if not pokemons[k]['ailment']=='fainting'])

            print('ポケモン\t:', active_pokemon['name'], f"(Lv:{active_pokemon['level']})")
            print('タイプ\t:', active_pokemon['types'])
            print('ﾃﾗｽﾀﾙ化\t:', active_pokemon['is_tera'])
            print('HP\t:', f"{active_pokemon['H']}/{active_pokemon['max_H']}")
            print('状態異常\t:', f"{active_pokemon['ailment']}")
            print()
            print('控え匹数\t:', f"{waiting_num}")
            print()
    
    """ポケモン交代"""
    # else:
        