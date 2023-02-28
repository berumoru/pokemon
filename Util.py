# 五捨五超入
def half_cut(num):
    
    delta = num - int(num)
    
    if delta <= 0.5:
        return int(num)
    else:
        return int(num) + 1