import numpy as np

import Visualize

# エージェントは現在の状態から、行動を決定する
def response_action(state, request, auto=False):

    # 現在のフェーズを参照
    phase = state['system_info']['phase']
    # 現在のプロセスを参照
    process = state['system_info']['process']
    
    # 選択肢を初期化
    selection = []
    
    """交代ポケモンの選択肢を取得"""
    # 手持ちのポケモンを参照
    pokemons = state[f'{request}_info']['pokemons']
    # 場に出ているポケモンを参照
    active_pokemon_id = state[f'{request}_info']['active_pokemon_id']
    # 場に出てこれないポケモンを参照
    disable_activate_pokemon_id = state[f'{request}_info']['disable_activate_pokemon_id']

    # 交代可能なポケモンの選択肢を取得
    enable_pokemons = {}
    for key in range(3):
        # 既に場に出ているポケモン or さっきまで場に出ていたポケモン or ひんしのポケモン は除外
        if (key == active_pokemon_id) or (key == disable_activate_pokemon_id) or (pokemons[key]['ailment'] == 'fainting'):
            continue
        enable_pokemons[f'pokemon_{key}'] = pokemons[key]['name']

    # 場に出てこれないポケモンをリセット
    state[f'{request}_info']['disable_activate_pokemon_id'] = -1
    # 選択肢に追加
    selection = list(enable_pokemons.keys())
    """"""

    # ポケモン交代プロセス
    if process == f'process__set_exchange':
        pass

    # 通常の行動選択フェーズ
    elif phase == f'phase__set_action':
        """技の選択肢を取得"""
        # 場に出ているポケモンを参照
        active_pokemon = pokemons[active_pokemon_id]
        # 技を参照
        moves = state[f'{request}_info']['pokemons'][active_pokemon_id]['moves']
        # 技の選択肢を取得
        enable_moves = {}
        for key in range(4):
            # 現時点ではPP切れなど未実装
            enable_moves[f'move_{key}'] = moves[key]['name']
        
        # 選択肢に追加
        selection += list(enable_moves.keys())
        
        # テラスタル
        if state[f'{request}_info']['tera_orb'] == 'unused':
            # 選択肢に追加
            selection += [f'{move}_tera' for move in enable_moves.keys()]
        
        """"""
        
    else:
        raise Exception

    if auto == False:
        # 現在の状態の表示
        print()
        print('----------現在の状態----------')
        Visualize.visualize_state(state, phase, request)
        print()

        print('----------')    
        print(f'プレイヤー{request} の行動を選択してください(半角英数字記号)：')
        if phase == f'phase__set_action':
            if state[f'{request}_info']['tera_orb'] == 'unused':
                print(f'テラスタル化したい場合は、選択肢の後ろに「_tera」と入力してください')
            print()
            print(enable_moves)
        print(enable_pokemons)
        print()

        # 行動を指定
        while True:
            action = input(f'action{request}>')
            if action in selection:
                break
            if action == 'debug':
                print('デバッグモードにより強制終了します。')
                break
            print(' 指定された行動は選択肢にありません。')
            print(' もう一度、選択肢の中から行動を指定してください。')
            print()
    else:
        # 現時点では完全ランダム
        # action = np.random.choice(selection)
        # デバッグ用
        action = 'move_2'
        

    return action