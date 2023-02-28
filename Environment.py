import numpy as np
import time
import pandas as pd
import copy

import Util


# 各種データ
# 急所ランク
critical_ranks = {
    0: 1/24,
    1: 1/8,
    2: 1/2,
    3: 1
}
# 能力ランク
status_ranks = {
    -5: 2/7,
    -4: 2/6,
    -3: 2/5,
    -2: 2/4,
    -1: 2/3,
    0: 2/2,
    1: 3/2,
    2: 4/2,
    3: 5/2,
    4: 6/2,
    5: 7/2,
    6: 8/2,
}
# 命中ランク
accuracy_ranks = {
    -6: 3/9,
    -5: 3/8,
    -4: 3/7,
    -3: 3/6,
    -2: 3/5,
    -1: 3/4,
    0: 3/3,
    1: 4/3,
    2: 5/3,
    3: 6/3,
    4: 7/3,
    5: 8/3,
    6: 9/3,
}

 # エージェントの行動と現在の状態から、次の状態を決定
def update_state(state, action):

    for _ in range(100):
        # デバッグ用
        phase = state['system_info']['phase']
        process = state['system_info']['process']
        update_battle_order_flag = state['system_info']['update_battle_order_flag']
        # print()
        # if update_battle_order_flag:
        #     print('point:', 'update_battle_order',)
        # elif process == '':
        #     print('point:', phase, ':', state['system_info']['phase_target'])
        # else:
        #     print('point:', process, ':', state['system_info']['process_target'])

        # エージェントの行動が必要になるまで、環境内部で状態を更新
        state, request = __update_state_internal(state, action)

        # エージェントの行動が必要になったら、ループ脱出
        if not request == 0:
            break

    return state, request


# 環境内部で状態を更新
def __update_state_internal(state, action):
    # 現在のフェーズを参照
    phase = state['system_info']['phase']
    # 現在のプロセスを参照
    process = state['system_info']['process']
    # 現在のフェーズ処理対象を参照
    phase_target = state['system_info']['phase_target']
    # 現在のプロセス処理対象を参照
    process_target = state['system_info']['process_target']
    # 処理順更新フラグ
    update_battle_order_flag = state['system_info']['update_battle_order_flag']

    # 処理順更新が必要な場合
    if update_battle_order_flag:
        # 処理順を更新
        state, request = __update_battle_order(state)

    # プロセス（割り込み処理）が指定されていない場合
    elif process == '':
        # 指定されたフェーズで状態を更新
        state, request = __update_by_phase(state, action, phase, phase_target)

    # プロセス（割り込み処理）が指定されている場合
    else:
        # 指定されたプロセスで状態を更新
        state, request = __update_by_process(state, action, process, process_target)

    return state, request


# 指定されたフェーズで状態を更新
def __update_by_phase(state, action, phase, target):

    # デバッグ用
    if phase == 'phase__by_debug':
        return state, 'end_judgement'


# ------------------------------対戦開始処理------------------------------

    # 対戦開始
    elif phase == 'phase__battle_start':
        # デバッグ用
        # state['system_info']['debug_value'] = True
        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__check_action'
        # 次のプロセスを指定
        state['system_info']['process'] = 'process__activate_pokemon'
        # コメント
        print('comment:', '対戦開始！')
        # 更新した状態を返す
        return state, 0


# ------------------------------行動選択処理------------------------------

    # プレイヤーの行動可否の確認
    elif phase == 'phase__check_action':

        # プレイヤーを参照
        player = state[f'{target}_info']
        # 場に出ているポケモンを参照
        active_pokemon_id = player['active_pokemon_id']
        active_pokemon = player['pokemons'][active_pokemon_id]
        # ポケモンの状態変化を参照
        active_pokemon_conditions = active_pokemon['conditions']

        # 反動で動けない場合
        if False:
            state[f'{target}_info']['selected_move_id'] = -1
            is_actionable = False

        # ため技の攻撃ターンの場合
        elif False:
            is_actionable = False
        
        # 状態変化「あばれる」状態の場合
        elif 'rage' in active_pokemon_conditions.keys():
            is_actionable = False

        # 行動可能な場合
        else:
            state[f'{target}_info']['selected_move_id'] = -1
            is_actionable = True
            
        
        # フラグ代入
        state[f'{target}_info']['is_actionable'] = is_actionable

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__request_action'

        # 更新した状態を返す
        return state, 0

    
    # プレイヤーに行動決定を要求
    elif phase == 'phase__request_action':

        # 行動可能かどうか
        is_actionable = state[f'{target}_info']['is_actionable']

        # 可能の場合、プレイヤーに行動決定を要求
        request = target if is_actionable else 0

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__set_action'

        # 更新した状態を返す
        return state, request


    # プレイヤーの行動を状態に保管
    elif phase == 'phase__set_action':

        # 行動可能かどうか
        is_actionable = state[f'{target}_info']['is_actionable']

        # 行動可能の場合
        if is_actionable:
            # 行動タイプ(技or交代)
            action_type = action.split('_')[0]
            action_id = int(action.split('_')[1])
            tera = action.split('_')[-1]
            # 技の場合
            if action_type == 'move':
                state[f'{target}_info']['selected_move_id'] = action_id
                # テラスタル化する場合
                state[f'{target}_info']['selected_tera'] = True if tera=='tera' else False
            # 交代の場合
            elif action_type == 'pokemon':
                state[f'{target}_info']['activate_pokemon_id'] = action_id
            else:
                raise Exception

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
                # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__request_action'
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__effect_by_ability_0'

        # 更新した状態を返す
        return state, 0


# ------------------------------行動前フェーズ------------------------------

    # 特性による効果
    elif phase == 'phase__effect_by_ability_0':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__effect_by_item_0'
            
        # 更新した状態を返す
        return state, 0

    
    # 持ち物による効果
    elif phase == 'phase__effect_by_item_0':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__damage_by_attack'
            
        # 更新した状態を返す
        return state, 0


    # 「おいうち」によるダメージ
    elif phase == 'phase__damage_by_attack':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__use_tera_orb'
            
        # 更新した状態を返す
        return state, 0

    
    # テラスタル化
    elif phase == 'phase__use_tera_orb':

        # テラスタル化する場合
        if state[f'{target}_info']['selected_tera']:
            # フラグを折る
            state[f'{target}_info']['selected_tera'] = False
            # プレイヤーを参照
            player = state[f'{target}_info']
            # テラスタルオーブを使用済みにする
            state[f'{target}_info']['tera_orb'] = 'used'
            # ポケモンを参照
            active_pokemon_id = player['active_pokemon_id']
            attack_pokemon = player['pokemons'][active_pokemon_id]
            # 元タイプを保管
            original_types = copy.deepcopy(attack_pokemon['types'])
            player['pokemons'][active_pokemon_id]['original_types'] = original_types
            # テラスタイプに上書き
            tera_type = copy.deepcopy(attack_pokemon['tera_type'])
            attack_pokemon['types'] = [tera_type]
            # テラスタル化フラグを立てる
            attack_pokemon['is_tera'] = True
            # コメント
            print('comment:', f"プレイヤー{target} の {attack_pokemon['name']} は テラスタルオーブ で {tera_type}タイプ になった！")

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__exchange_pokemon'
            
        # 更新した状態を返す
        return state, 0


    # プレイヤーのポケモンを交代
    elif phase == 'phase__exchange_pokemon':
        
        # 交代待機がいるかどうか
        activate_pokemon_id = state[f'{target}_info']['activate_pokemon_id']
        if not activate_pokemon_id == -1:
            # 引っ込めるポケモンを参照
            active_pokemon_id = state[f'{target}_info']['active_pokemon_id']
            active_pokemon = state[f'{target}_info']['pokemons'][active_pokemon_id]
            # コメント
            print('comment:', f"「プレイヤー{target} は {active_pokemon['name']} を引っ込めた！」")
            # 場に出ているポケモンを引っ込める
            state[f'{target}_info']['active_pokemon_id'] = -1
            # 次の処理対象を指定
            state['system_info']['process_target'] = target
            # 次のフェーズを指定
            state['system_info']['process'] = 'process__activate_pokemon'

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_move_order'
            
        # 更新した状態を返す
        return state, 0


    # 行動順判定
    elif phase == 'phase__judge_move_order':
        # 初期化
        move_order = ['A', 'B']
        selected_move_ids = {}
        priorities = {}
        speeds = {}

        for player in move_order:
            active_pokemon_id = state[f'{player}_info']['active_pokemon_id']
            selected_move_id = state[f'{player}_info']['selected_move_id']
            # 選択された技を参照
            selected_move_ids[player] = selected_move_id
            if selected_move_id == -1:
                continue
            active_pokemon = state[f'{player}_info']['pokemons'][active_pokemon_id]
            # 優先度を参照
            priorities[player] = active_pokemon['moves'][selected_move_id]['priority']
            # 素早さを参照
            speeds[player] = active_pokemon['S']
        
        # 技を選択していない場合
        if (selected_move_ids['A'] == -1) & (selected_move_ids['B'] == -1):
            state['system_info']['move_order'] = []
        elif selected_move_ids['B'] == -1:
            state['system_info']['move_order'] = ['A']
        elif selected_move_ids['A'] == -1:
            state['system_info']['move_order'] = ['B']

        # 優先度に差がある場合
        elif priorities['A'] > priorities['B']:
            state['system_info']['move_order'] = move_order
        elif priorities['A'] < priorities['B']:
            state['system_info']['move_order'] = move_order[::-1]

        # 素早さに差がある場合
        elif speeds['A'] > speeds['B']:
            state['system_info']['move_order'] = move_order
        elif speeds['A'] < speeds['B']:
            state['system_info']['move_order'] = move_order[::-1]
        
        # ランダムに行動順を決定
        else:
            rnd = np.random.rand()
            state['system_info']['move_order'] = move_order if rnd > 0.5 else move_order[::-1]


        move_order = state['system_info']['move_order']
        if len(move_order) == 0:
            # 次の処理対象を指定
            battle_order = state['system_info']['battle_order']
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_weather_stopped'
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = move_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_move_success'
            
        # 更新した状態を返す
        return state, 0

    
# ------------------------------行動フェーズ------------------------------

    # 技成功判定
    elif phase == 'phase__judge_move_success':
        # 初期化
        is_successful = True
        request = 0
        
        """成功判定"""
        # break用
        for _ in [None]:
            # 技使用側のプレイヤーを参照
            attack_player = state[f'{target}_info']
            # 技使用側のポケモンを参照
            active_pokemon_id = attack_player['active_pokemon_id']
            attack_pokemon = attack_player['pokemons'][active_pokemon_id]
            # 使用する技を参照
            move_id = attack_player['selected_move_id']
            move = attack_pokemon['moves'][move_id]
            # 技使用側のポケモンの状態異常を参照
            attack_pokemon_ailment = attack_pokemon['ailment']
            # 技使用側のポケモンの状態変化を参照
            attack_pokemon_conditions = attack_pokemon['conditions']

            # 乱数生成
            rand = np.random.rand()
            
            # 状態変化「こんらん」のターン消費
            if 'confusion' in attack_pokemon_conditions.keys():
                # コメント
                print('comment:', f"プレイヤー{target} の {attack_pokemon['name']} は こんらん している。")
                # ターン消費
                attack_pokemon_conditions['confusion'] -= 1
                confusion_count = attack_pokemon_conditions['confusion']
                # 「こんらん」解除
                if confusion_count <= 0:
                    # 「こんらん」を削除
                    del attack_pokemon_conditions['confusion']
                    # コメント
                    print('comment:', f"プレイヤー{target} の {attack_pokemon['name']} の こんらんが とけた！")
            

            # 状態異常「こおり」の場合、20%の確率で回復
            if attack_pokemon_ailment == 'frozen':
                if rand < 0.2:
                    # コメント
                    print('comment:', f"プレイヤー{target} の {attack_pokemon['name']} の こおりが とけた！")
                else:
                    # コメント
                    print('comment:', f"プレイヤー{target} の {attack_pokemon['name']} の からだが こおっていて うごけない。")
                    is_successful = False
                    break

            # 状態異常「まひ」の場合、1/4で失敗
            if (attack_pokemon_ailment == 'paralysis') & (rand < 1/4):
                # コメント
                print('comment:', f"プレイヤー{target} の {attack_pokemon['name']} は からだが しびれて うごけない。")
                is_successful = False
                break
            
            # 状態変化「こんらん」による失敗
            if ('confusion' in attack_pokemon_conditions.keys()) & (rand < 1/2):
                print('comment:', f"プレイヤー{target} の {attack_pokemon['name']} は わけもわからず じぶんを　こうげき した。")
                # 技使用側のポケモンのレベルを参照
                attack_pokemon_level = attack_pokemon['level']
                # 物理攻撃ステータスを参照
                attack_pokemon_A = attack_pokemon['A']
                # 物理防御ステータスを参照
                attack_pokemon_B = attack_pokemon['B']
                # 体力ステータスを参照
                attack_pokemon_H = attack_pokemon['H']
                # 乱数補正
                random_rate = np.random.randint(85, 101) / 100
                # ダメージ計算
                damage = int(attack_pokemon_level * 2/5 + 2)
                damage = int(damage * 40 * attack_pokemon_A / attack_pokemon_B)
                damage = int(damage / 50 + 2)
                damage =  int(damage * random_rate)
                # ダメージを受ける
                delta = attack_pokemon_H - damage
                attack_pokemon['H'] = delta if delta >0 else 0
                # 「ひんし」になった場合
                if attack_pokemon['H'] <= 0:
                    # テラスタルを解除
                    if attack_pokemon['is_tera']:
                        types = copy.deepcopy(attack_pokemon['original_types'])
                        attack_pokemon['types'] = types
                        del attack_pokemon['original_types']
                        attack_pokemon['is_tera'] = False
                    # 状態異常を「ひんし」にする
                    attack_pokemon['ailment'] = 'fainting'
                    # 状態変化をリセット
                    attack_pokemon['conditions'] = {}
                    # 場から退場
                    attack_player['active_pokemon_id'] = -1
                    # 次のプロセス処理対象を指定
                    state['system_info']['process_target'] = target
                    # 次のプロセスを指定
                    state['system_info']['process'] = 'process__request_exchange'
                    # 終了判定を依頼
                    request = 'end_judgement'
                    # コメント
                    print('comment:', f"プレイヤー{target} の {attack_pokemon['name']} は たおれた！")
                # 成功フラグを折る
                is_successful = False
                break

            # 技使用のメッセージ
            # コメント
            print('comment:', f"プレイヤー{target} の {attack_pokemon['name']} の {move['name']} ！")

            # PPを消費する
            move['PP'] = move['PP'] - 1
            
            # 技のタイプが変わる場合
            #　テラバーストに対応予定
            
            # 状態変化「みがわり」状態で技「みがわり」を使用した場合
            if ('substitude' in attack_pokemon_conditions.keys()) & (move['name'] == 'みがわり'):
                print('comment:', f"プレイヤー{target} の {attack_pokemon['name']} は すでに みがわりを だしている。")
                is_successful = False
                break

            # タイプ相性によって失敗
            # 防御側のプレイヤーを参照
            opponent = 'A' if target=='B' else 'B'
            defence_player = state[f'{opponent}_info']
            # 技使用側のポケモンを参照
            defence_pokemon_id = defence_player['active_pokemon_id']
            defence_pokemon = defence_player['pokemons'][defence_pokemon_id]
            # 防御側のタイプを参照
            defence_types = defence_pokemon['types']
            # 「でんじは」を除く、変化技の場合はスキップ
            if (move['is_attack']) | (move['name']=='でんじは'):
                # 使用する技のタイプを参照
                move_type = move['type']
                # タイプ相性表の読み込み
                df_type = pd.read_csv('type.csv', index_col=0).T
                # タイプ相性を計算
                defence_type_match_rate = 1.0
                for defence_type in defence_types:
                    defence_type_match_rate *= df_type[move_type][defence_type]
                # 技が無効の場合
                if defence_type_match_rate == 0.0:
                    # コメント
                    print('comment:', f"プレイヤー{opponent} の {defence_pokemon['name']} には こうかが ないようだ。")
                    is_successful = False
                    break
            
            # 技を外したことによる失敗
            accuracy_rank = attack_pokemon['accuracy_rank']
            # 命中ランクを範囲内にキャッピング
            if accuracy_rank < -6:
                accuracy_rank = -6
            elif accuracy_rank > 6:
                accuracy_rank = 6
            # 命中率を計算
            accuracy = int(move['accuracy'] * accuracy_ranks[accuracy_rank])
            accuracy = accuracy if accuracy < 100 else 100
            # 外した場合
            if not (accuracy > np.random.randint(100)):
                # コメント
                print('comment:', f"プレイヤー{opponent} の {defence_pokemon['name']} には 当たらなかった。")
                is_successful = False
                break
            
            # 状態異常「ねむり」でないときに「ねごと」を使い、失敗
            if (move['name'] == 'ねごと') & (not attack_pokemon_ailment == 'sleep'):
                # コメント
                print('comment:', f"プレイヤー{target} の {attack_pokemon['name']} は 起きている。")
                is_successful = False
                break
        
        # 成功した場合
        if is_successful:

            # 状態変化「あばれる」状態に"今から"なる場合
            if (move['name'] in ['げきりん']) & ('rage' not in attack_pokemon['conditions'].keys()):
                attack_pokemon['conditions']['rage'] = np.random.randint(2,4)

            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__calculate_combo_limit'

        # 失敗した場合
        else:
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__move_end'
            
        # 更新した状態を返す
        return state, request

    
    # 変化技の効果
    elif phase == 'phase__status_move':

        # 攻撃側プレイヤーを参照
        player = state[f'{target}_info']
        # 攻撃側のポケモンを参照
        active_pokemon_id = player['active_pokemon_id']
        active_pokemon = player['pokemons'][active_pokemon_id]
        # 攻撃側の技を参照
        move_id = player['selected_move_id']
        move = active_pokemon['moves'][move_id]
        # 攻撃側の状態変化を参照
        conditions = active_pokemon['conditions']

        # 変化技の場合
        if not move['is_attack']:
            # 技「みがわり」の場合
            if move['name'] in ['みがわり']:
                # 状態変化「みがわり」状態になる
                active_pokemon['conditions']['substitude'] = np.inf
            
        # 攻撃技の場合
        else:
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__calculate_combo_limit'
            # プレイヤーへの要求は無し
            request = 0
        
        return state, request
    

    # 連続攻撃回数計算
    elif phase == 'phase__calculate_combo_limit':
        # 技使用側のプレイヤーを参照
        attack_player = state[f'{target}_info']
        # 技使用側のポケモンを参照
        active_pokemon_id = attack_player['active_pokemon_id']
        attack_pokemon = attack_player['pokemons'][active_pokemon_id]
        # 使用する技を参照
        move_id = attack_player['selected_move_id']
        move = attack_pokemon['moves'][move_id]

        # 連続技の場合
        if ('is_combo', True) in move.items():
            # 乱数を生成
            rand = np.random.rand()
            # 回数を計算
            combo_limit = 0
            if rand <= 0.35:
                combo_limit = 2
            elif rand <= 0.70:
                combo_limit = 3
            elif rand <= 0.85:
                combo_limit = 4
            else:
                combo_limit = 5
            # 攻撃カウントを保管
            attack_player['combo_count'] = 0
            attack_player['combo_limit'] = combo_limit
            attack_player['ongoing_combo'] = True
    
        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__calculate_damage'

        # 更新した状態を返す
        return state, 0
    
    
    # ダメージ計算
    elif phase == 'phase__calculate_damage':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__recoil_before_damage'

        """ダメージ計算"""
        # 技使用側のプレイヤーを参照
        attack_player = state[f'{target}_info']
        # 技使用側のポケモンを参照
        active_pokemon_id = attack_player['active_pokemon_id']
        attack_pokemon = attack_player['pokemons'][active_pokemon_id]
        # 使用する技を参照
        move_id = attack_player['selected_move_id']
        move = attack_pokemon['moves'][move_id]

        # 変化技の場合
        if not move['is_attack']:
            state['system_info']['damage'] = np.nan
            # 更新した状態を返す
            return state, 0
        
        # 攻撃側のレベルを参照
        attack_pokemon_level = attack_pokemon['level']
        # 攻撃技の基礎威力を参照
        base_power = move['power']
        # テラスタル化フラグを参照
        is_tera = attack_pokemon['is_tera']
        # 攻撃側のタイプを参照
        attack_pokemon_types = attack_pokemon['types'] if not is_tera else [attack_pokemon['tera_type']]
        # 攻撃技の分類(物理or特殊）を参照
        move_category = move['move_category']
        # 攻撃技のタイプを参照
        move_type = move['type']
        # 攻撃側の攻撃ステータスを参照
        attack = attack_pokemon['A'] if move_category=='physical' else attack_pokemon['C']
        # 攻撃側の急所ランクを参照
        critical_rank = attack_pokemon['critical_rank'] + move['critical_rank']
        # 攻撃側の状態異常を参照
        attack_pokemon_ailment = attack_pokemon['ailment']
        # 攻撃側の持ち物を参照
        attack_pokemon_item = attack_pokemon['item']

        # 防御側のプレイヤーを参照
        opponent = 'A' if target=='B' else 'B'
        defence_player = state[f'{opponent}_info']
        # 技使用側のポケモンを参照
        defence_pokemon_id = defence_player['active_pokemon_id']
        defence_pokemon = defence_player['pokemons'][defence_pokemon_id]
        # 防御側の防御ステータスを参照
        defence = defence_pokemon['B'] if move_category=='physical' else attack_pokemon['D']
        defence_max_H = defence_pokemon['max_H']
        defence_H = defence_pokemon['H']
        # 防御側のタイプを参照
        defence_types = defence_pokemon['types']
        # 防御側の状態変化を参照
        defence_conditions = defence_pokemon['conditions'].keys()
        # 防御側の持ち物を参照
        defence_pokemon_item = defence_pokemon['item']
        
        # 全体の情報を参照
        all_info = state['all_info']
        # 天候を参照
        weather = all_info['weather']
        # タイプ相性表の読み込み
        df_type = pd.read_csv('type.csv', index_col=0).T


        # 天候による補正を計算
        weather_rate = 1.0
        
        # 急所ランクによる補正を計算
        critical_prob = critical_ranks[critical_rank if critical_rank < 3 else 3]
        critical_rate = 1.5 if critical_prob > np.random.rand() else 1.0
        # 急所補正の結果を保管
        state['system_info']['critical_rate'] = critical_rate
        
        # 乱数による補正を計算
        random_rate = np.random.randint(85, 101) / 100
        
        # タイプ一致による補正
        if move_type in attack_pokemon_types:
            # テラスタル化していて、元タイプと一致している場合
            if attack_pokemon['tera_type_match']:
                attack_type_match_rate = 2.0
            # タイプ一致している場合
            else:
                attack_type_match_rate = 1.5
        # タイプ不一致
        else:
            attack_type_match_rate = 1.0
        
        # タイプ相性による補正
        defence_type_match_rate = 1.0
        for defence_type in defence_types:
            defence_type_match_rate *= df_type[move_type][defence_type]
        # 相性の結果を保管
        state['system_info']['defence_type_match_rate'] = defence_type_match_rate
        
        # やけどによる補正
        if (move_category == 'physical') & (attack_pokemon_ailment == 'burn'):
            burn_rate = 0.5
        else:
            burn_rate = 1.0
        
        # 「いのちのたま」による補正
        life_orb_rate = 1.3 if attack_pokemon_item == 'いのちのたま' else 1.0
        
        # 威力を補正する
        # 別個計算用の関数を用意する？ move と自分と相手の特性を渡す
        if (attack_pokemon_item == 'くろいメガネ') & (move_type == 'dark'):
            power_rate = 4915/4096
        else:
            power_rate = 1.0
        power = np.round(base_power * power_rate)
        
        # ダメージを計算
        damage = int(attack_pokemon_level * 2/5 + 2)
        damage = int(damage * power * attack / defence)
        damage = int(damage / 50 + 2)
        damage =  Util.half_cut(damage * weather_rate)
        damage =  Util.half_cut(damage * critical_rate)
        damage =  int(damage * random_rate)
        damage =  Util.half_cut(damage * attack_type_match_rate)
        damage =  int(damage * defence_type_match_rate)
        damage =  Util.half_cut(damage * burn_rate)
        M = life_orb_rate
        damage = Util.half_cut(damage * M)
        
        """"""
        """最終補正"""
        # ダメージが 0 になった場合
        damage = damage if not damage==0 else 1

        # 身代わりの場合
        if 'substitude' in defence_conditions:
            pass
        # 上記以外
        else:
            damage = damage if damage < defence_H else defence_H

        # 何らかの効果により、H=1で耐えられる場合
        # 「きあいのたすき」の場合
        if (defence_pokemon_item == 'きあいのタスキ') & (defence_H == defence_max_H) & (damage >= defence_H):
            damage = defence_H - 1
            # きあいのタスキ使用フラグを立てる
            state['system_info']['used_focus_sash_flag'] = True
        
        
        """"""

        # ダメージを代入
        state['system_info']['damage'] = damage
            
        # 更新した状態を返す
        return state, 0


    # 与ダメージ前反動
    elif phase == 'phase__recoil_before_damage':
        # あとで実装
        pass
        
        # 被ダメージ側のポケモンの状態変化を参照
        opponent = 'A' if target=='B' else 'B'
        opponent_active_pokemon_id = state[f'{opponent}_info']['active_pokemon_id']
        opponent_active_pokemon = state[f'{opponent}_info']['pokemons'][opponent_active_pokemon_id]
        opponent_active_pokemon_conditions = opponent_active_pokemon['conditions'].keys()

        # 次のフェーズを指定
        # 被ダメージ側のポケモンがみがわり状態かどうか
        if 'substitude' in opponent_active_pokemon_conditions:
            state['system_info']['phase'] = 'phase__damage_to_substitude'
        else:
            state['system_info']['phase'] = 'phase__inflict_damage'

        # 更新した状態を返す
        return state, 0


    # みがわりにダメージ
    elif phase == 'phase__damage_to_substitude':
        
        # 被ダメージ側のポケモンの状態変化を参照
        opponent = 'A' if target=='B' else 'B'
        opponent_active_pokemon_id = state[f'{opponent}_info']['active_pokemon_id']
        opponent_active_pokemon = state[f'{opponent}_info']['pokemons'][opponent_active_pokemon_id]
        opponent_active_pokemon_conditions = opponent_active_pokemon['conditions']
        
        # 被ダメージ側のポケモンがみがわり状態の場合
        if 'substitude' in opponent_active_pokemon_conditions.keys():
            # 次のフェーズを指定
            state['system_info']['phase'] = ''
        else:
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__inflict_damage'
            
        # 更新した状態を返す
        return state, 0


    # 相手にダメージ
    elif phase == 'phase__inflict_damage':
        
        # ダメージを参照
        damage = state['system_info']['damage']
        
        # 与ダメージ側のポケモンの技を参照
        active_pokemon_id = state[f'{target}_info']['active_pokemon_id']
        move_id = state[f'{target}_info']['selected_move_id']
        active_pokemon = state[f'{target}_info']['pokemons'][active_pokemon_id]
        move = active_pokemon['moves'][move_id]
        
        # 被ダメージ側のポケモンのHPを参照
        opponent = 'A' if target=='B' else 'B'
        opponent_active_pokemon_id = state[f'{opponent}_info']['active_pokemon_id']
        opponent_active_pokemon = state[f'{opponent}_info']['pokemons'][opponent_active_pokemon_id]
        opponent_active_pokemon_H = opponent_active_pokemon['H']

        # 与ダメージ（ひんし判定はここでは行わない）
        opponent_active_pokemon['H'] = opponent_active_pokemon_H - damage

        # 連続攻撃カウント
        if ('is_combo', True) in move.items():
            state[f'{target}_info']['combo_count'] += 1

        # H がゼロになった時間を覚えておく
        if opponent_active_pokemon['H'] <= 0:
            state[f'{opponent}_info']['fainted_time'] = time.time()
        
        # 効果バツグンの場合
        if (state['system_info']['defence_type_match_rate'] > 1.0):
            print('comment:', f"効果は バツグン だ！")

        # 効果いまひとつの場合
        elif state['system_info']['defence_type_match_rate'] < 1.0:
            print('comment:', f"効果は いまひとつ のようだ！")

        # 急所に当たった場合
        if state['system_info']['critical_rate'] > 1.0:
            print('comment:', f"急所にあたった！！")

        # 「きあいのたすき」で持ち堪えた場合
        if ('used_focus_sash_flag', True) in state['system_info'].items():
            print('comment:', f"{opponent_active_pokemon} は もちこたえた！")
            print('きあいのたすき が なくなった。')
            state[f'{opponent}_info']['pokemons'][opponent_active_pokemon_id]['item'] = ''
            state['system_info']['used_focus_sash_flag'] = False

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_by_attack_1'

        # 更新した状態を返す
        return state, 0


    # 技の追加効果の発動
    elif phase == 'phase__effect_by_attack_1':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_by_damage'

        # 更新した状態を返す
        return state, 0

    
    # ダメージによる追加効果の発動
    elif phase == 'phase__effect_by_damage':
        # TODO
        if state['system_info']['damage'] > 0:
            # 攻撃側のポケモンを参照
            active_pokemon_id = state[f'{target}_info']['active_pokemon_id']
            active_pokemon = state[f'{opponent}_info']['pokemons'][active_pokemon_id]
            # 攻撃側のポケモンの技を参照
            move_id = state[f'{target}_info']['selected_move_id']
            move = active_pokemon['moves'][move_id]
            # 攻撃側のステータスを参照
            active_pokemon_max_H = active_pokemon['max_H']
            active_pokemon_H = active_pokemon['H']

            # 防御側のポケモンを参照
            opponent = 'A' if target=='B' else 'B'
            opponent_active_pokemon_id = state[f'{opponent}_info']['active_pokemon_id']
            opponent_active_pokemon = state[f'{opponent}_info']['pokemons'][opponent_active_pokemon_id]
            # 防御側の特性を参照
            opponent_active_pokemon_ability = opponent_active_pokemon['ability']
            # 防御側のポケモンの持ち物を参照
            opponent_active_pokemon_item = opponent_active_pokemon['item']

            # 防御側のポケモンの特性が「さめはだ」で、
            # 攻撃側のポケモンの技が接触技の場合
            if (opponent_active_pokemon_ability['name'] == ['さめはだ']) & move['is_contact']:
                print('comment:', f"プレイヤー{target} の {active_pokemon['name']} は さめはだの ダメージを うけた！")
                # ダメージ量計算
                damage = int(active_pokemon_max_H / 8)
                # ダメージを受ける
                delta = active_pokemon_H - damage
                active_pokemon['H'] = delta if delta > 0 else 0
                # 「ひんし」になった場合
                if active_pokemon['H'] <= 0:
                    # テラスタルを解除
                    if attack_pokemon['is_tera']:
                        types = copy.deepcopy(active_pokemon['original_types'])
                        active_pokemon['types'] = types
                        del active_pokemon['original_types']
                        active_pokemon['is_tera'] = False
                    # 状態異常を「ひんし」にする
                    active_pokemon['ailment'] = 'fainting'
                    # 状態変化をリセット
                    active_pokemon['conditions'] = {}
                    # 場から退場
                    state[f'{target}_info']['active_pokemon_id'] = -1
                    # 次のプロセス処理対象を指定
                    state['system_info']['process_target'] = target
                    # 次のプロセスを指定
                    state['system_info']['process'] = 'process__request_exchange'
                    # 終了判定を依頼
                    request = 'end_judgement'
                    # コメント
                    print('comment:', f"プレイヤー{target} の {active_pokemon['name']} は たおれた！")
            
            # 防御側のポケモンがゴツゴツメットを持っていて、
            # 攻撃側のポケモンの技が接触技の場合
            if (opponent_active_pokemon_item['name'] == ['ゴツゴツメット']) & move['is_contact']:
                print('comment:', f"プレイヤー{target} の {active_pokemon['name']} は ゴツゴツメット の ダメージを うけた！")
                # ダメージ量計算
                damage = int(active_pokemon_max_H / 6)
                # ダメージを受ける
                delta = active_pokemon_H - damage
                active_pokemon['H'] = delta if delta > 0 else 0
                # 「ひんし」になった場合
                if active_pokemon['H'] <= 0:
                    # テラスタルを解除
                    if attack_pokemon['is_tera']:
                        types = copy.deepcopy(active_pokemon['original_types'])
                        active_pokemon['types'] = types
                        del active_pokemon['original_types']
                        active_pokemon['is_tera'] = False
                    # 状態異常を「ひんし」にする
                    active_pokemon['ailment'] = 'fainting'
                    # 状態変化をリセット
                    active_pokemon['conditions'] = {}
                    # 場から退場
                    state[f'{target}_info']['active_pokemon_id'] = -1
                    # 次のプロセス処理対象を指定
                    state['system_info']['process_target'] = target
                    # 次のプロセスを指定
                    state['system_info']['process'] = 'process__request_exchange'
                    # 終了判定を依頼
                    request = 'end_judgement'
                    # コメント
                    print('comment:', f"プレイヤー{target} の {active_pokemon['name']} は たおれた！")

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__judge_fainted'

        # 更新した状態を返す
        return state, 0
    
    
    # ひんし判定
    elif phase == 'phase__judge_fainted':
        # 状態異常「ひんし」になった時刻を参照
        target_fainted_time = state[f'{target}_info']['fainted_time']
        opponent = 'A' if target=='B' else 'B'
        opponent_fainted_time = state[f'{opponent}_info']['fainted_time']

        # 「ひんし」が発生していない場合
        if (target_fainted_time == np.inf) & (opponent_fainted_time == np.inf):
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_combo_loop'
            # 更新した状態を返す
            return state, 0

        # 連続技で「ひんし」が発生している場合
        if ('ongoing_combo', True) in state[f'{target}_info'].items():
            # 「ひんし」発生フラグを立てる
            state['system_info']['is_fainting'] = True
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_combo_loop'
            # 更新した状態を返す
            return state, 0

        # 「ひんし」処理対象の決定
        if target_fainted_time < opponent_fainted_time:
            player = target
        elif target_fainted_time > opponent_fainted_time:
            player = opponent



        # 「ひんし」処理
        # テラスタルを解除
        active_pokemon_id = state[f'{player}_info']['active_pokemon_id']
        active_pokemon = state[f'{player}_info']['pokemons'][active_pokemon_id]
        if active_pokemon['is_tera']:
            types = copy.deepcopy(active_pokemon['original_types'])
            active_pokemon['types'] = types
            del active_pokemon['original_types']
            active_pokemon['is_tera'] = False
        # 状態異常を「ひんし」にする
        active_pokemon['ailment'] = 'fainting'
        # ひんしタイミングをリセット
        state[f'{player}_info']['fainted_time'] = np.inf
        # 状態変化をリセット
        active_pokemon['conditions'] = {}
        # 場から退場
        state[f'{player}_info']['active_pokemon_id'] = -1
        # プレイヤーに行動決定の要求
        state['system_info']['process'] = 'process__request_exchange'
        # コメント
        print('comment:', f"プレイヤー{player} の {active_pokemon['name']} は たおれた！")

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__judge_fainted'
        # 次のフェーズ処理対象を指定
        state['system_info']['process_target'] = player
        # 更新した状態を返す
        return state, 'end_judgement'
    
    
    # 連続攻撃ループ判定
    elif phase == 'phase__judge_combo_loop':
        # 連続攻撃かどうか
        player = state[f'{target}_info']
        active_pokemon_id = player['active_pokemon_id']
        move_id = player['selected_move_id']
        active_pokemon = player['pokemons'][active_pokemon_id]
        move = active_pokemon['moves'][move_id]
        # 連続攻撃の場合
        if ('is_combo', True) in move.items():
            combo_count = player['combo_count']
            combo_limit = player['combo_limit']
            # きのみ等の発動判定
            pass
            # 「ひんし」が発生している場合
            if ('is_fainting', True) in state['system_info'].items():
                # 「ひんし」発生フラグを折る
                state['system_info']['is_fainting'] = False
                # コメント
                print('comment:', f"{combo_count}回 当たった！")
                # 連続攻撃を終了
                player['ongoing_combo'] = False
                player['combo_count'] = 0
                player['combo_limit'] = 0
                # 次のフェーズを指定
                state['system_info']['phase'] = 'phase__judge_fainted'
            # 「ひんし」が発生していない場合
            else:
                # 攻撃回数の上限に達している場合
                if combo_count >= combo_limit:
                    # コメント
                    print('comment:', f"{combo_count}回 当たった！")
                    # 連続攻撃を終了
                    player['ongoing_combo'] = False
                    player['combo_count'] = 0
                    player['combo_limit'] = 0
                    # 次のフェーズを指定
                    state['system_info']['phase'] = 'phase__recoil_after_damage'
                # まだ攻撃回数を残している場合
                else:
                    # 次のフェーズを指定
                    state['system_info']['phase'] = 'phase__calculate_damage'
        # 通常攻撃の場合
        else:
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recoil_after_damage'

        # 更新した状態を返す
        return state, 0


    # 攻撃後反動
    elif phase == 'phase__recoil_after_damage':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_by_attack_2'

        # 更新した状態を返す
        return state, 0


    # 技の追加効果の発動
    elif phase == 'phase__effect_by_attack_2':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_by_ability_1'

        # 更新した状態を返す
        return state, 0


    # 特性の効果発動
    elif phase == 'phase__effect_by_ability_1':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_by_item_1'

        # 更新した状態を返す
        return state, 0


    # 持ち物の効果発動
    elif phase == 'phase__effect_by_item_1':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__recoil_by_item'

        # 更新した状態を返す
        return state, 0


    # 持ち物による反動
    elif phase == 'phase__recoil_by_item':
        
        # プレイヤーを参照
        player = state[f'{target}_info']
        # ポケモンを参照
        active_pokemon_id = player['active_pokemon_id']
        active_pokemon = player['pokemons'][active_pokemon_id]
        # 持ち物を参照
        item = active_pokemon['item']
        # いのちのたまを持っている場合
        if item == 'いのちのたま':
            # 最大HPを参照
            active_pokemon_max_H = active_pokemon['max_H']
            # ダメージを計算
            damage = int(active_pokemon_max_H / 10)
            # HPを参照
            active_pokemon_H = active_pokemon['H']
            # ダメージを受ける
            delta = active_pokemon_H - damage
            active_pokemon['H'] = delta if delta >0 else 0
            # コメント
            print('comment:', f"プレイヤー{target} の {active_pokemon['name']} は いのちのたま の はんどう をうけた！")
            # 「ひんし」になった場合
            if active_pokemon['H'] <= 0:
                # テラスタルを解除
                if active_pokemon['is_tera']:
                    types = copy.deepcopy(active_pokemon['original_types'])
                    active_pokemon['types'] = types
                    del active_pokemon['original_types']
                    active_pokemon['is_tera'] = False
                # 状態異常を「ひんし」にする
                active_pokemon['ailment'] = 'fainting'
                # 状態変化をリセット
                active_pokemon['conditions'] = {}
                # 場から退場
                player['active_pokemon_id'] = -1
                # 次のプロセス処理対象を指定
                state['system_info']['process_target'] = target
                # 次のプロセスを指定
                state['system_info']['process'] = 'process__request_exchange'
                # 終了判定を依頼
                request = 'end_judgement'
                # コメント
                print('comment:', f"プレイヤー{target} の {active_pokemon['name']} は たおれた！")

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__recover_by_item_1'

        # 更新した状態を返す
        return state, 0


    #　持ち物による回復
    elif phase == 'phase__recover_by_item_1':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_by_item_2'

        # 更新した状態を返す
        return state, 0


    #　持ち物の効果発動
    elif phase == 'phase__effect_by_item_2':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__exchange_by_ability_1'

        # 更新した状態を返す
        return state, 0


    #　特性によるポケモン交代
    elif phase == 'phase__exchange_by_ability_1':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__exchange_by_ability_2'

        # 更新した状態を返す
        return state, 0


    # 特性によるポケモン交代
    elif phase == 'phase__exchange_by_ability_2':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_by_ability_2'

        # 更新した状態を返す
        return state, 0


    # 特性の効果発動
    elif phase == 'phase__effect_by_ability_2':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_by_attack_3'

        # 更新した状態を返す
        return state, 0


    # 技の効果発動
    elif phase == 'phase__effect_by_attack_3':
        active_pokemon_id = state[f'{target}_info']['active_pokemon_id']
        active_pokemon = state[f'{target}_info']['pokemons'][active_pokemon_id]
        active_pokemon_conditions = active_pokemon['conditions']
        
        # 状態変化「あばれる」状態のターン消費または終了による状態異常「こんらん」
        if 'rage' in active_pokemon_conditions.keys():
            # ターン数消費
            active_pokemon_conditions['rage'] -= 1
            rage_count = active_pokemon_conditions['rage']
            
            # 「あばれる」状態終了の場合
            if rage_count <= 0:
                # 「あばれる」状態を削除
                del active_pokemon_conditions['rage']
                # 「こんらん」状態になる
                active_pokemon_conditions['confusion'] = np.random.randint(2, 6)
                # コメント
                print('comment:', f"プレイヤー{target} の {active_pokemon['name']} は つかれはてて こんらん した！")
                
        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_by_item_3'

        # 更新した状態を返す
        return state, 0


    # 持ち物の効果発動
    elif phase == 'phase__effect_by_item_3':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_by_ability_3'

        # 更新した状態を返す
        return state, 0


    # 特性の効果発動
    elif phase == 'phase__effect_by_ability_3':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_after_move_by_item'

        # 更新した状態を返す
        return state, 0


    # 行動後に発動する持ち物の効果
    elif phase == 'phase__effect_after_move_by_item':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_by_ability_4'

        # 更新した状態を返す
        return state, 0


    # 特性の効果発動
    elif phase == 'phase__effect_by_ability_4':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__move_end'

        # 更新した状態を返す
        return state, 0

    
    # 行動終了
    elif phase == 'phase__move_end':

        # 保管しているダメージをリセット
        state['system_info']['damage'] = 0
        # 行動していたプレイヤーを行動順から削除
        del state['system_info']['move_order'][0]
        # 行動順を参照
        move_order = state['system_info']['move_order']
        if len(move_order) == 0:
            # 次の処理対象を指定
            battle_order = state['system_info']['battle_order']
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_weather_stopped'
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = move_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_move_success'
            
        # 更新した状態を返す
        return state, 0


# ------------------------------完了フェーズ------------------------------

    # 天候終了判定
    elif phase == 'phase__judge_weather_stopped':
        
        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__damage_by_weather'
        
        # 更新した状態を返す
        return state, 0


    # 天候ダメージ
    elif phase == 'phase__damage_by_weather':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__effect_by_weather'

        # 更新した状態を返す
        return state, 0


    # 天候の効果
    elif phase == 'phase__effect_by_weather':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__exchange_by_ability_3'

        # 更新した状態を返す
        return state, 0


    # 特性によるポケモン交代
    elif phase == 'phase__exchange_by_ability_3':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__damage_by_past_move'

        # 更新した状態を返す
        return state, 0


    # 「みらいよち」などの過去からのダメージ
    elif phase == 'phase__damage_by_past_move':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recover_by_past_move'

        # 更新した状態を返す
        return state, 0


    # 「ねがいごと」などの過去からの回復
    elif phase == 'phase__recover_by_past_move':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__damage_by_only_field'

        # 更新した状態を返す
        return state, 0


    # 片側の場の状態のよるダメージ
    elif phase == 'phase__damage_by_only_field':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recover_by_all_field'

        # 更新した状態を返す
        return state, 0


    # 場の状態による回復
    elif phase == 'phase__recover_by_all_field':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recover_by_ability'

        # 更新した状態を返す
        return state, 0


    # 特性による回復
    elif phase == 'phase__recover_by_ability':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recover_by_item_2'

        # 更新した状態を返す
        return state, 0


    # 持ち物による回復
    elif phase == 'phase__recover_by_item_2':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__exchange_by_ability_4'

        # 更新した状態を返す
        return state, 0


    # 特性によるポケモン交代
    elif phase == 'phase__exchange_by_ability_4':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recover_by_condition_1'

        # 更新した状態を返す
        return state, 0


    # 状態変化による回復
    elif phase == 'phase__recover_by_condition_1':
        
        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recover_by_condition_2'

        # 更新した状態を返す
        return state, 0


    # 状態変化による回復
    elif phase == 'phase__recover_by_condition_2':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recover_by_condition_3'

        # 更新した状態を返す
        return state, 0


    # 状態変化による回復
    elif phase == 'phase__recover_by_condition_3':
        
        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__damage_by_ailment_1'

        # 更新した状態を返す
        return state, 0

    
    # 状態異常によるダメージ
    elif phase == 'phase__damage_by_ailment_1':
        
        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__damage_by_ailment_2'

        # 更新した状態を返す
        return state, 0


    #　状態異常によるダメージ
    elif phase == 'phase__damage_by_ailment_2':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__recover_by_condition_4'

        # 更新した状態を返す
        return state, 0


    # 状態変化による回復
    elif phase == 'phase__recover_by_condition_4':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recover_by_condition_5'

        # 更新した状態を返す
        return state, 0


    # 状態変化による回復
    elif phase == 'phase__recover_by_condition_5':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recover_by_condition_6'

        # 更新した状態を返す
        return state, 0


    # 状態変化による回復
    elif phase == 'phase__recover_by_condition_6':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recover_by_condition_7'

        # 更新した状態を返す
        return state, 0


    # 状態変化による回復
    elif phase == 'phase__recover_by_condition_7':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recover_by_condition_8'

        # 更新した状態を返す
        return state, 0


    # 状態変化による回復
    elif phase == 'phase__recover_by_condition_8':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_condition_count_1'

        # 更新した状態を返す
        return state, 0


    #　状態変化の終了判定
    elif phase == 'phase__judge_condition_count_1':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_condition_count_2'

        # 更新した状態を返す
        return state, 0


    # 状態変化の終了判定
    elif phase == 'phase__judge_condition_count_2':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_condition_count_3'

        # 更新した状態を返す
        return state, 0


    # 状態変化の終了判定
    elif phase == 'phase__judge_condition_count_3':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_condition_count_4'

        # 更新した状態を返す
        return state, 0


    # 状態変化の終了判定
    elif phase == 'phase__judge_condition_count_4':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_condition_count_5'

        # 更新した状態を返す
        return state, 0


    # 状態変化の終了判定
    elif phase == 'phase__judge_condition_count_5':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_condition_count_6'

        # 更新した状態を返す
        return state, 0


    # 状態変化の終了判定
    elif phase == 'phase__judge_condition_count_6':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_condition_count_7'

        # 更新した状態を返す
        return state, 0


    # 状態変化の終了判定
    elif phase == 'phase__judge_condition_count_7':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_condition_count_8'

        # 更新した状態を返す
        return state, 0


    # 状態変化の終了判定
    elif phase == 'phase__judge_condition_count_8':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_condition_count_9'

        # 更新した状態を返す
        return state, 0


    # 状態変化の終了判定
    elif phase == 'phase__judge_condition_count_9':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_condition_count_10'

        # 更新した状態を返す
        return state, 0


    # 状態変化の終了判定
    elif phase == 'phase__judge_condition_count_10':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__recover_type'

        # 更新した状態を返す
        return state, 0


    # 「はねやすめ」による消失した「ひこうタイプ」の回復
    elif phase == 'phase__recover_type':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__exchange_by_ability_5'

        # 更新した状態を返す
        return state, 0


    # 特性によるポケモン交代
    elif phase == 'phase__exchange_by_ability_5':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_only_field_count_1'

        # 更新した状態を返す
        return state, 0


    # 片側の場の状態の終了判定
    elif phase == 'phase__judge_only_field_count_1':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_only_field_count_2'

        # 更新した状態を返す
        return state, 0


    # 片側の場の状態の終了判定
    elif phase == 'phase__judge_only_field_count_2':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_only_field_count_3'

        # 更新した状態を返す
        return state, 0


    # 片側の場の状態の終了判定
    elif phase == 'phase__judge_only_field_count_3':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_only_field_count_4'

        # 更新した状態を返す
        return state, 0


    # 片側の場の状態の終了判定
    elif phase == 'phase__judge_only_field_count_4':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_only_field_count_5'

        # 更新した状態を返す
        return state, 0


    # 片側の場の状態の終了判定
    elif phase == 'phase__judge_only_field_count_5':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_only_field_count_6'

        # 更新した状態を返す
        return state, 0


    # 片側の場の状態の終了判定
    elif phase == 'phase__judge_only_field_count_6':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_only_field_count_7'

        # 更新した状態を返す
        return state, 0


    # 片側の場の状態の終了判定
    elif phase == 'phase__judge_only_field_count_7':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_only_field_count_8'

        # 更新した状態を返す
        return state, 0


    # 片側の場の状態の終了判定
    elif phase == 'phase__judge_only_field_count_8':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_only_field_count_9'

        # 更新した状態を返す
        return state, 0


    # 片側の場の状態の終了判定
    elif phase == 'phase__judge_only_field_count_9':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_only_field_count_10'

        # 更新した状態を返す
        return state, 0


    # 片側の場の状態の終了判定
    elif phase == 'phase__judge_only_field_count_10':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__judge_all_field_count_1'

        # 更新した状態を返す
        return state, 0


    # 場の状態の終了判定
    elif phase == 'phase__judge_all_field_count_1':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__judge_all_field_count_2'

        # 更新した状態を返す
        return state, 0


    # 場の状態の終了判定
    elif phase == 'phase__judge_all_field_count_2':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__judge_all_field_count_3'

        # 更新した状態を返す
        return state, 0


    # 場の状態の終了判定
    elif phase == 'phase__judge_all_field_count_3':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__judge_all_field_count_4'

        # 更新した状態を返す
        return state, 0


    # 場の状態の終了判定
    elif phase == 'phase__judge_all_field_count_4':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__judge_all_field_count_5'

        # 更新した状態を返す
        return state, 0


    # 場の状態の終了判定
    elif phase == 'phase__judge_all_field_count_5':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__judge_all_field_count_6'

        # 更新した状態を返す
        return state, 0


    # 場の状態の終了判定
    elif phase == 'phase__judge_all_field_count_6':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__judge_all_field_count_7'

        # 更新した状態を返す
        return state, 0


    # 場の状態の終了判定
    elif phase == 'phase__judge_all_field_count_7':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__effect_by_condition'

        # 更新した状態を返す
        return state, 0


    # 状態変化の効果
    elif phase == 'phase__effect_by_condition':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__effect_by_ailment'

        # 更新した状態を返す
        return state, 0


    # 状態異常による効果
    elif phase == 'phase__effect_by_ailment':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__effect_by_ability_5'

        # 更新した状態を返す
        return state, 0


    # 特性による変化
    elif phase == 'phase__effect_by_ability_5':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__effect_by_item_4'

        # 更新した状態を返す
        return state, 0


    # 持ち物による効果
    elif phase == 'phase__effect_by_item_4':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__effect_by_ability_6'

        # 更新した状態を返す
        return state, 0


    # 特性による変化
    elif phase == 'phase__effect_by_ability_6':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__effect_by_item_5'

        # 更新した状態を返す
        return state, 0


    # 持ち物による効果
    elif phase == 'phase__effect_by_item_5':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__exchange_by_ability_6'

        # 更新した状態を返す
        return state, 0


    # 特性によるポケモン交代
    elif phase == 'phase__exchange_by_ability_6':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__form_change_1'

        # 更新した状態を返す
        return state, 0


    # フォームチェンジ
    elif phase == 'phase__form_change_1':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__form_change_2'

        # 更新した状態を返す
        return state, 0


    # フォームチェンジ
    elif phase == 'phase__form_change_2':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__exchange_by_item'

        # 更新した状態を返す
        return state, 0


    # 持ち物によるポケモン交代
    elif phase == 'phase__exchange_by_item':

        # 次の処理対象を決定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[1]
        else:
            # 次の処理対象を指定
            state['system_info']['phase_target'] = battle_order[0]
            # 次のフェーズを指定
            state['system_info']['phase'] = 'phase__turn_end'

        # 更新した状態を返す
        return state, 0


    # ターン完了
    elif phase == 'phase__turn_end':

        # 次のフェーズを指定
        state['system_info']['phase'] = 'phase__check_action'

        # 更新した状態を返す
        return state, 0
    
    
    # 想定されていないフェーズ（エラー処理を書く予定）
    else:
        raise Exception


        
        
        
        
        
        
        











# 指定されたプロセスで状態を更新
def __update_by_process(state, action, process, target):

    # デバッグ用
    if process == 'process__by_debug':
        return state, 'end_judgement'


    # プレイヤーに交代するポケモンの決定を要求
    elif process == 'process__request_exchange':

        # 次のフェーズを指定
        state['system_info']['process'] = 'process__set_exchange'

        # 更新した状態を返す
        return state, target


    # プレイヤーの決定を保管
    elif process == 'process__set_exchange':
        
        # プレイヤーの決定を保管
        state[f'{target}_info']['activate_pokemon_id'] = int(action.split('_')[1])

        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        state['system_info']['process_target'] = battle_order[0]
        # 次のフェーズを指定
        state['system_info']['process'] = 'process__activate_pokemon'

        # 更新した状態を返す
        return state, 0


    # ポケモン繰り出し処理
    elif process == 'process__activate_pokemon':
        
        # 場に出ているポケモンがいるかどうか
        if state[f'{target}_info']['active_pokemon_id'] == -1:
            # ポケモンを繰り出す
            activate_pokemon_id = state[f'{target}_info']['activate_pokemon_id']
            state[f'{target}_info']['active_pokemon_id'] = activate_pokemon_id
            active_pokemon = state[f'{target}_info']['pokemons'][activate_pokemon_id]
            # コメント
            print('comment:', f"プレイヤー{target} は {active_pokemon['name']} を繰り出した！")

        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 処理順更新フラグを立てる
            state['system_info']['update_battle_order_flag'] = True
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__effect_by_ability_1'
            

        # 更新した状態を返す
        return state, 0

    
    # 特性による効果
    elif process == 'process__effect_by_ability_1':
        
        # このプロセスでポケモンを繰り出したかどうか
        if not state[f'{target}_info']['activate_pokemon_id'] == -1:
            pass
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__effect_by_ability_2'
        
        # 更新した状態を返す
        return state, 0

    
    # 特性による効果
    elif process == 'process__effect_by_ability_2':
            
        # このプロセスでポケモンを繰り出したかどうか
        if not state[f'{target}_info']['activate_pokemon_id'] == -1:
            pass
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__recover_by_past_move'
        
        # 更新した状態を返す
        return state, 0
    
    
    # 「癒しの願い」等による回復
    elif process == 'process__recover_by_past_move':
            
        # このプロセスでポケモンを繰り出したかどうか
        if not state[f'{target}_info']['activate_pokemon_id'] == -1:
            pass
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__damage_by_trap'
        
        # 更新した状態を返す
        return state, 0
    
    
    # 設置技によるダメージ
    elif process == 'process__damage_by_trap':
            
        # このプロセスでポケモンを繰り出したかどうか
        if not state[f'{target}_info']['activate_pokemon_id'] == -1:
            pass
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__effect_by_ability_3'
        
        # 更新した状態を返す
        return state, 0
    
    
    # 特性による効果
    elif process == 'process__effect_by_ability_3':
            
        # このプロセスでポケモンを繰り出したかどうか
        if not state[f'{target}_info']['activate_pokemon_id'] == -1:
            pass
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__effect_by_ability_4'
        
        # 更新した状態を返す
        return state, 0
    
    
    # 特性による効果
    elif process == 'process__effect_by_ability_4':
            
        # このプロセスでポケモンを繰り出したかどうか
        if not state[f'{target}_info']['activate_pokemon_id'] == -1:
            # 場に出ているポケモンを参照
            active_pokemon_id = state[f'{target}_info']['active_pokemon_id']
            active_pokemon = state[f'{target}_info']['pokemons'][active_pokemon_id]
            # ポケモンの特性を参照
            active_pokemon_ability = active_pokemon['ability']
            # 特性「いかく」の場合
            if active_pokemon_ability == 'いかく':
                # 相手のポケモンを参照
                opponent = 'A' if target=='B' else 'B'
                opponent_active_pokemon_id = state[f'{opponent}_info']['active_pokemon_id']
                opponent_active_pokemon = state[f'{opponent}_info']['pokemons'][opponent_active_pokemon_id]
                # 相手のポケモンの攻撃ランクを1段階下げる
                opponent_A_rank = copy.deepcopy(opponent_active_pokemon['A_rank'])
                opponent_A_rank -= 1
                opponent_A_rank = opponent_A_rank if opponent_A_rank >=-6 else -6
                # 元の攻撃力を保管
                if opponent_active_pokemon['A_rank'] == 0:
                    opponent_active_pokemon['original_A'] = copy.deepcopy(opponent_active_pokemon['A'])
                # 攻撃力を補正
                if not opponent_active_pokemon['A_rank'] == opponent_A_rank:
                    opponent_active_pokemon['A'] = int(opponent_active_pokemon['original_A'] * status_ranks[opponent_A_rank])
                # 攻撃ランクを保管
                opponent_active_pokemon['A_rank'] = opponent_A_rank
                # コメント
                print('comment:', f"プレイヤー{opponent} の {opponent_active_pokemon['name']} は いかく されて 攻撃が １だんかい　さがった。")
                    

        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__effect_by_ability_5'
        
        # 更新した状態を返す
        return state, 0


    # 特性による効果
    elif process == 'process__effect_by_ability_5':
        
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__effect_by_item_1'
        
        # 更新した状態を返す
        return state, 0
    
    
    # 持ち物による効果
    elif process == 'process__effect_by_item_1':
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__form_change'
        
        # 更新した状態を返す
        return state, 0
    
    
    # フォルムチェンジ
    elif process == 'process__form_change':
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__effect_by_item_2'
        
        # 更新した状態を返す
        return state, 0
    
    
    # 持ち物による効果
    elif process == 'process__effect_by_item_2':
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__effect_by_item_3'
        
        # 更新した状態を返す
        return state, 0
    
    
    # 持ち物による効果
    elif process == 'process__effect_by_item_3':
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__effect_by_item_4'
        
        # 更新した状態を返す
        return state, 0
 

    # 持ち物による効果
    elif process == 'process__effect_by_item_4':
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__effect_by_item_5'
        
        # 更新した状態を返す
        return state, 0

    
    # 持ち物による効果
    elif process == 'process__effect_by_item_5':
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__effect_by_ability_6'
        
        # 更新した状態を返す
        return state, 0
    
    
    # 特性による効果
    elif process == 'process__effect_by_ability_6':
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__effect_by_item_6'
        
        # 更新した状態を返す
        return state, 0
    
    
    # 持ち物による効果
    elif process == 'process__effect_by_item_6':
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__exchange_by_item'
        
        # 更新した状態を返す
        return state, 0
    
    
    # 持ち物によるポケモン交代
    elif process == 'process__exchange_by_item':
            
        # 次の処理対象を指定
        battle_order = state['system_info']['battle_order']
        if battle_order[0] == target:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[1]
        # 上記以外
        else:
            # 次の処理対象を指定
            state['system_info']['process_target'] = battle_order[0]
            # 次のプロセスを指定
            state['system_info']['process'] = 'process__end'
        
        # 更新した状態を返す
        return state, 0


    # プロセス終了
    elif process == 'process__end':
        
        
        # 交換待機フラグを折る
        for player in ['A', 'B']:
            state[f'{player}_info']['activate_pokemon_id'] = -1
        # 処理対象をリセット
        state['system_info']['process_target'] = ''
        # プロセスをリセット
        state['system_info']['process'] = ''
        
        # 更新した状態を返す
        return state, 0
    
    
    # 想定されていないプロセス（エラー処理を書く予定）
    else:
        raise Exception

        
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
# 処理順を更新
def __update_battle_order(state):
    # 初期化
    battle_order = ['A', 'B']
    speeds = {}

    # 素早さを参照
    for player in battle_order:
        active_pokemon_id = state[f'{player}_info']['active_pokemon_id']
        speeds[player] = state[f'{player}_info']['pokemons'][active_pokemon_id]['S']

    # 素早さに差がある場合
    if speeds['A'] > speeds['B']:
        state['system_info']['battle_order'] = battle_order
    elif speeds['A'] < speeds['B']:
        state['system_info']['battle_order'] = battle_order[::-1]
    # 素早さに差がない場合
    else:
        rnd = np.random.rand()
        state['system_info']['battle_order'] = battle_order if rnd > 0.5 else battle_order[::-1]

    # フェーズ処理対象の更新
    state['system_info']['phase_target'] = state['system_info']['battle_order'][0]
    # 処理順更新フラグを折る
    state['system_info']['update_battle_order_flag'] = False

    # 更新した状態を返す
    return state, 0