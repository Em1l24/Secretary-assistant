import re
import zipfile
import os
from datetime import datetime


def normalize_fio(fio):
    """Нормализация ФИО: заглавные буквы, убирание лишних пробелов"""
    if not fio:
        return fio
    return ' '.join(word.strip().title() for word in str(fio).split() if word.strip())


def get_gender_from_fio(fio):
    """Определение пола по ФИО"""
    if not fio:
        return None
    
    parts = str(fio).split()
    
    # Попытка определить по отчеству
    if len(parts) >= 3:
        middle_name = parts[2].lower()
        if middle_name.endswith(('ич', 'ович', 'евич')):
            return 'male'
        elif middle_name.endswith(('на', 'вна')):
            return 'female'
    
    # Попытка определить по имени
    if len(parts) >= 2:
        first_name = parts[1].lower()
        
        female_names = {
            'софья', 'софия', 'ульяна', 'татьяна', 'ксения', 'оксана', 'евгения',
            'александра', 'валерия', 'вероника', 'дарья', 'елена', 'зинаида',
            'ирина', 'марина', 'надежда', 'ольга', 'светлана', 'юлия', 'яна',
            'алиса', 'ангелина', 'анна', 'василиса', 'галина', 'диана',
            'екатерина', 'елизавета', 'инна', 'карина', 'клара', 'кристина',
            'любовь', 'людмила', 'маргарита', 'мария', 'настасья', 'наталья',
            'нина', 'полина', 'раиса', 'регина', 'рената', 'снежана', 'стелла',
            'сусана', 'тамара', 'эвелина', 'эльвира', 'эмилия', 'юлиана', 'ярослава'
        }
        
        male_names = {
            'павел', 'данил', 'даниил', 'гаврил', 'михаил', 'кирилл', 'владимир',
            'вячеслав', 'станислав', 'ростислав', 'ярослав', 'мстислав', 'святослав',
            'бронислав', 'лев', 'пётр', 'петр', 'юрий', 'сергей', 'георгий', 'демьян',
            'илья', 'игорь', 'андрей', 'алексей', 'евгений', 'константин', 'никита',
            'вадим', 'василий', 'григорий', 'максим', 'роман', 'тимур', 'эдуард',
            'яков', 'денис', 'артём', 'артем', 'гордей', 'руслан', 'ренат', 'влад',
            'владислав', 'антон', 'алан', 'александр'
        }
        
        if first_name in female_names:
            return 'female'
        elif first_name in male_names:
            return 'male'
    
    return None


def _get_lastname_declension_rules():
    """Возвращает правила для склонения фамилий"""
    return {
        'non_declining_any_gender': {
            'гемель', 'дежурко', 'шмидт', 'буш', 'фрейд', 'гейтс', 'хуго',
            'якоб', 'гёте', 'мендель', 'дарвин', 'коперник', 'галилей'
        },
        'non_declining_suffixes_any_gender': ['ко', 'енко'],
        'male_only_declining_suffixes': ['чук', 'юк', 'ук', 'чак', 'як'],
        'non_declining_suffixes_no_gender': ['их', 'ых', 'аго', 'яго', 'ово']
    }


def _should_decline_lastname(last_lower, is_female):
    """Определяет, нужно ли склонять фамилию"""
    rules = _get_lastname_declension_rules()
    
    if last_lower in rules['non_declining_any_gender']:
        return False
    
    for suffix in rules['non_declining_suffixes_any_gender']:
        if last_lower.endswith(suffix):
            return False
    
    for suffix in rules['non_declining_suffixes_no_gender']:
        if last_lower.endswith(suffix):
            return False
    
    for suffix in rules['male_only_declining_suffixes']:
        if last_lower.endswith(suffix):
            return not is_female  # Склоняем только для мужского рода
    
    return True


def _decline_lastname(last_name, is_female, case):
    """
    Склонение фамилии
    case: 'genitive', 'dative', 'accusative'
    """
    if not _should_decline_lastname(last_name.lower(), is_female):
        return last_name
    
    last_lower = last_name.lower()
    
    # Настройки окончаний для разных падежей
    endings = {
        'genitive': {
            'female_ov': 'ой', 'female_sk': 'ой', 'female_con': '',
            'male_ov': 'а', 'male_sk': 'ого', 'male_con': 'а'
        },
        'dative': {
            'female_ov': 'ой', 'female_sk': 'ой', 'female_con': '',
            'male_ov': 'у', 'male_sk': 'ому', 'male_con': 'у'
        },
        'accusative': {
            'female_ov': 'у', 'female_sk': 'ую', 'female_con': '',
            'male_ov': 'а', 'male_sk': 'ого', 'male_con': 'а'
        }
    }
    
    if is_female:
        if last_lower.endswith(('ова', 'ева', 'ина', 'ына')):
            return last_name[:-1] + endings[case]['female_ov']
        elif last_lower.endswith(('ская', 'кая')):
            return last_name[:-2] + endings[case]['female_sk']
        elif last_lower.endswith('ая'):
            return last_name[:-2] + endings[case]['female_sk']
        elif last_lower.endswith('яя'):
            return last_name[:-2] + ('ей' if case == 'genitive' else 'юю' if case == 'accusative' else 'ей')
        elif last_lower.endswith(('б', 'в', 'г', 'д', 'ж', 'з', 'к', 'л', 'м',
                                  'н', 'п', 'р', 'с', 'т', 'ф', 'х', 'ц', 'ч', 'ш', 'щ')):
            return last_name
        else:
            return last_name
    else:
        if last_lower.endswith(('ов', 'ев', 'ёв', 'ин', 'ын')):
            return last_name + endings[case]['male_ov']
        elif last_lower.endswith(('ский', 'цкий', 'кой')):
            return last_name[:-2] + endings[case]['male_sk']
        elif last_lower.endswith(('ая', 'ый', 'ой')):
            return last_name[:-2] + endings[case]['male_sk']
        elif last_lower.endswith(('б', 'в', 'г', 'д', 'ж', 'з', 'к', 'л', 'м',
                                  'н', 'п', 'р', 'с', 'т', 'ф', 'х', 'ц', 'ч', 'ш', 'щ')):
            return last_name + endings[case]['male_con']
        elif last_lower.endswith('чук'):
            return last_name[:-3] + ('чука' if case != 'dative' else 'чуку')
        elif last_lower.endswith('юк'):
            return last_name[:-2] + ('юка' if case != 'dative' else 'юку')
        elif last_lower.endswith('ук'):
            return last_name[:-2] + ('ука' if case != 'dative' else 'уку')
        elif last_lower.endswith('чак'):
            return last_name[:-3] + ('чака' if case != 'dative' else 'чаку')
        elif last_lower.endswith('як'):
            return last_name[:-2] + ('яка' if case != 'dative' else 'яку')
        else:
            return last_name + endings[case]['male_con']


def to_genitive(fio):
    """Преобразование ФИО в родительный падеж (кого? чего?)"""
    if not fio:
        return fio
    
    fio_norm = normalize_fio(fio)
    parts = fio_norm.split()
    
    if len(parts) != 3:
        return fio_norm
    
    last_name, first_name, middle_name = parts
    gender = get_gender_from_fio(fio_norm)
    is_female = (gender == 'female') if gender else middle_name.endswith(('на', 'вна'))
    
    # Исключения для имен
    first_name_exceptions = {
        'павел': 'Павла', 'данил': 'Данила', 'даниил': 'Даниила', 'гаврил': 'Гаврила',
        'михаил': 'Михаила', 'кирилл': 'Кирилла', 'владимир': 'Владимира',
        'вячеслав': 'Вячеслава', 'станислав': 'Станислава', 'ростислав': 'Ростислава',
        'ярослав': 'Ярослава', 'мстислав': 'Мстислава', 'святослав': 'Святослава',
        'бронислав': 'Бронислава', 'лев': 'Льва', 'пётр': 'Петра', 'петр': 'Петра',
        'юрий': 'Юрия', 'сергей': 'Сергея', 'георгий': 'Георгия', 'демьян': 'Демьяна',
        'илья': 'Ильи', 'игорь': 'Игоря', 'андрей': 'Андрея', 'алексей': 'Алексея',
        'евгений': 'Евгения', 'константин': 'Константина', 'никита': 'Никиты',
        'вадим': 'Вадима', 'василий': 'Василия', 'григорий': 'Григория',
        'максим': 'Максима', 'роман': 'Романа', 'тимур': 'Тимура', 'эдуард': 'Эдуарда',
        'яков': 'Якова', 'денис': 'Дениса', 'артём': 'Артёма', 'артем': 'Артема',
        'гордей': 'Гордея', 'руслан': 'Руслана', 'ренат': 'Рената', 'влад': 'Влада',
        'владислав': 'Владислава', 'антон': 'Антона', 'алан': 'Алана',
        'александр': 'Александра', 'софья': 'Софьи', 'софия': 'Софии',
        'ульяна': 'Ульяны', 'татьяна': 'Татьяны', 'ксения': 'Ксении', 'оксана': 'Оксаны',
        'евгения': 'Евгении', 'александра': 'Александры', 'валерия': 'Валерии',
        'вероника': 'Вероники', 'дарья': 'Дарьи', 'елена': 'Елены', 'зинаида': 'Зинаиды',
        'ирина': 'Ирины', 'марина': 'Марины', 'надежда': 'Надежды', 'ольга': 'Ольги',
        'светлана': 'Светланы', 'юлия': 'Юлии', 'яна': 'Яны', 'алиса': 'Алисы',
        'ангелина': 'Ангелины', 'анна': 'Анны', 'василиса': 'Василисы', 'галина': 'Галины',
        'диана': 'Дианы', 'екатерина': 'Екатерины', 'елизавета': 'Елизаветы',
        'инна': 'Инны', 'карина': 'Карины', 'клара': 'Клары', 'кристина': 'Кристины',
        'любовь': 'Любови', 'людмила': 'Людмилы', 'маргарита': 'Маргариты',
        'мария': 'Марии', 'настасья': 'Настасьи', 'наталья': 'Натальи', 'нина': 'Нины',
        'полина': 'Полины', 'раиса': 'Раисы', 'регина': 'Регины', 'рената': 'Ренаты',
        'снежана': 'Снежаны', 'стелла': 'Стеллы', 'сусана': 'Сусаны', 'тамара': 'Тамары',
        'эвелина': 'Эвелины', 'эльвира': 'Эльвиры', 'эмилия': 'Эмилии',
        'юлиана': 'Юлианы', 'ярослава': 'Ярославы'
    }
    
    first_lower = first_name.lower()
    if first_lower in first_name_exceptions:
        first_name_gen = first_name_exceptions[first_lower]
    elif is_female:
        if first_lower.endswith('а'):
            first_name_gen = first_name[:-1] + 'ы'
        elif first_lower.endswith('я'):
            first_name_gen = first_name[:-1] + 'и'
        elif first_lower.endswith('ь'):
            first_name_gen = first_name[:-1] + 'и'
        else:
            first_name_gen = first_name
    else:
        if first_lower.endswith('й'):
            first_name_gen = first_name[:-1] + 'я'
        elif first_lower.endswith('ь'):
            first_name_gen = first_name[:-1] + 'я'
        elif first_lower.endswith('а'):
            first_name_gen = first_name[:-1] + 'ы'
        elif first_lower.endswith('я'):
            first_name_gen = first_name[:-1] + 'и'
        elif first_lower.endswith('ел'):
            first_name_gen = first_name[:-2] + 'ла'
        elif first_lower.endswith('ил'):
            first_name_gen = first_name[:-2] + 'ила'
        else:
            first_name_gen = first_name + 'а'
    
    last_name_gen = _decline_lastname(last_name, is_female, 'genitive')
    
    if is_female:
        if middle_name.endswith(('на', 'вна')):
            middle_name_gen = middle_name[:-1] + 'ы'
        else:
            middle_name_gen = middle_name
    else:
        if middle_name.endswith(('ич', 'ович', 'евич')):
            middle_name_gen = middle_name + 'а'
        else:
            middle_name_gen = middle_name
    
    return f"{last_name_gen} {first_name_gen} {middle_name_gen}"


def to_dative(fio):
    """Преобразование ФИО в дательный падеж (кому? чему?)"""
    if not fio:
        return fio
    
    fio_norm = normalize_fio(fio)
    parts = fio_norm.split()
    
    if len(parts) != 3:
        return fio_norm
    
    last_name, first_name, middle_name = parts
    gender = get_gender_from_fio(fio_norm)
    is_female = (gender == 'female') if gender else middle_name.endswith(('на', 'вна'))
    
    first_name_exceptions = {
        'павел': 'Павлу', 'данил': 'Данилу', 'даниил': 'Даниилу', 'гаврил': 'Гаврилу',
        'михаил': 'Михаилу', 'кирилл': 'Кириллу', 'владимир': 'Владимиру',
        'вячеслав': 'Вячеславу', 'станислав': 'Станиславу', 'ростислав': 'Ростиславу',
        'ярослав': 'Ярославу', 'мстислав': 'Мстиславу', 'святослав': 'Святославу',
        'бронислав': 'Брониславу', 'лев': 'Льву', 'пётр': 'Петру', 'петр': 'Петру',
        'юрий': 'Юрию', 'сергей': 'Сергею', 'георгий': 'Георгию', 'демьян': 'Демьяну',
        'илья': 'Илье', 'игорь': 'Игорю', 'андрей': 'Андрею', 'алексей': 'Алексею',
        'евгений': 'Евгению', 'константин': 'Константину', 'никита': 'Никите',
        'вадим': 'Вадиму', 'василий': 'Василию', 'григорий': 'Григорию',
        'максим': 'Максиму', 'роман': 'Роману', 'тимур': 'Тимуру', 'эдуард': 'Эдуарду',
        'яков': 'Якову', 'денис': 'Денису', 'артём': 'Артёму', 'артем': 'Артему',
        'гордей': 'Гордею', 'руслан': 'Руслану', 'ренат': 'Ренату', 'влад': 'Владу',
        'владислав': 'Владиславу', 'антон': 'Антону', 'алан': 'Алану',
        'александр': 'Александру', 'софья': 'Софье', 'софия': 'Софии',
        'ульяна': 'Ульяне', 'татьяна': 'Татьяне', 'ксения': 'Ксении', 'оксана': 'Оксане',
        'евгения': 'Евгении', 'александра': 'Александре', 'валерия': 'Валерии',
        'вероника': 'Веронике', 'дарья': 'Дарье', 'елена': 'Елене', 'зинаида': 'Зинаиде',
        'ирина': 'Ирине', 'марина': 'Марине', 'надежда': 'Надежде', 'ольга': 'Ольге',
        'светлана': 'Светлане', 'юлия': 'Юлии', 'яна': 'Яне', 'алиса': 'Алисе',
        'ангелина': 'Ангелине', 'анна': 'Анне', 'василиса': 'Василисе', 'галина': 'Галине',
        'диана': 'Диане', 'екатерина': 'Екатерине', 'елизавета': 'Елизавете',
        'инна': 'Инне', 'карина': 'Карине', 'клара': 'Кларе', 'кристина': 'Кристине',
        'любовь': 'Любови', 'людмила': 'Людмиле', 'маргарита': 'Маргарите',
        'мария': 'Марии', 'настасья': 'Настасье', 'наталья': 'Наталье', 'нина': 'Нине',
        'полина': 'Полине', 'раиса': 'Раисе', 'регина': 'Регине', 'рената': 'Ренате',
        'снежана': 'Снежане', 'стелла': 'Стелле', 'сусана': 'Сусане', 'тамара': 'Тамаре',
        'эвелина': 'Эвелине', 'эльвира': 'Эльвире', 'эмилия': 'Эмилии',
        'юлиана': 'Юлиане', 'ярослава': 'Ярославе'
    }
    
    first_lower = first_name.lower()
    if first_lower in first_name_exceptions:
        first_name_dat = first_name_exceptions[first_lower]
    elif is_female:
        if first_lower.endswith(('а', 'я')):
            first_name_dat = first_name[:-1] + 'е'
        elif first_lower.endswith('ь'):
            first_name_dat = first_name[:-1] + 'и'
        else:
            first_name_dat = first_name
    else:
        if first_lower.endswith('й'):
            first_name_dat = first_name[:-1] + 'ю'
        elif first_lower.endswith('ь'):
            first_name_dat = first_name[:-1] + 'ю'
        elif first_lower.endswith(('а', 'я')):
            first_name_dat = first_name[:-1] + 'е'
        elif first_lower.endswith('ел'):
            first_name_dat = first_name[:-2] + 'лу'
        elif first_lower.endswith('ил'):
            first_name_dat = first_name[:-2] + 'илу'
        else:
            first_name_dat = first_name + 'у'
    
    last_name_dat = _decline_lastname(last_name, is_female, 'dative')
    
    if is_female:
        if middle_name.endswith(('на', 'вна')):
            middle_name_dat = middle_name[:-1] + 'е'
        else:
            middle_name_dat = middle_name
    else:
        if middle_name.endswith(('ич', 'ович', 'евич')):
            middle_name_dat = middle_name + 'у'
        else:
            middle_name_dat = middle_name
    
    return f"{last_name_dat} {first_name_dat} {middle_name_dat}"



def to_accusative(fio):
    """Преобразование ФИО в винительный падеж (кого? что?)"""
    if not fio:
        return fio
    
    fio_norm = normalize_fio(fio)
    parts = fio_norm.split()
    
    if len(parts) != 3:
        return fio_norm
    
    last_name, first_name, middle_name = parts
    gender = get_gender_from_fio(fio_norm)
    is_female = (gender == 'female') if gender else middle_name.endswith(('на', 'вна'))
    
    first_name_exceptions = {
        'павел': 'Павла', 'данил': 'Данила', 'даниил': 'Даниила', 'гаврил': 'Гаврила',
        'михаил': 'Михаила', 'кирилл': 'Кирилла', 'владимир': 'Владимира',
        'вячеслав': 'Вячеслава', 'станислав': 'Станислава', 'ростислав': 'Ростислава',
        'ярослав': 'Ярослава', 'мстислав': 'Мстислава', 'святослав': 'Святослава',
        'бронислав': 'Бронислава', 'лев': 'Льва', 'пётр': 'Петра', 'петр': 'Петра',
        'юрий': 'Юрия', 'сергей': 'Сергея', 'георгий': 'Георгия', 'демьян': 'Демьяна',
        'илья': 'Илью', 'игорь': 'Игоря', 'андрей': 'Андрея', 'алексей': 'Алексея',
        'евгений': 'Евгения', 'константин': 'Константина', 'никита': 'Никиту',
        'вадим': 'Вадима', 'василий': 'Василия', 'григорий': 'Григория',
        'максим': 'Максима', 'роман': 'Романа', 'тимур': 'Тимура', 'эдуард': 'Эдуарда',
        'яков': 'Якова', 'денис': 'Дениса', 'артём': 'Артёма', 'артем': 'Артема',
        'гордей': 'Гордея', 'руслан': 'Руслана', 'ренат': 'Рената', 'влад': 'Влада',
        'владислав': 'Владислава', 'антон': 'Антона', 'алан': 'Алана',
        'александр': 'Александра', 'софья': 'Софью', 'софия': 'Софию',
        'ульяна': 'Ульяну', 'татьяна': 'Татьяну', 'ксения': 'Ксению', 'оксана': 'Оксану',
        'евгения': 'Евгению', 'александра': 'Александру', 'валерия': 'Валерию',
        'вероника': 'Веронику', 'дарья': 'Дарью', 'елена': 'Елену', 'зинаида': 'Зинаиду',
        'ирина': 'Ирину', 'марина': 'Марину', 'надежда': 'Надежду', 'ольга': 'Ольгу',
        'светлана': 'Светлану', 'юлия': 'Юлию', 'яна': 'Яну', 'алиса': 'Алису',
        'ангелина': 'Ангелину', 'анна': 'Анну', 'василиса': 'Василису', 'галина': 'Галину',
        'диана': 'Диану', 'екатерина': 'Екатерину', 'елизавета': 'Елизавету',
        'инна': 'Инну', 'карина': 'Карину', 'клара': 'Клару', 'кристина': 'Кристину',
        'любовь': 'Любовь', 'людмила': 'Людмилу', 'маргарита': 'Маргариту',
        'мария': 'Марию', 'настасья': 'Настасью', 'наталья': 'Наталью', 'нина': 'Нину',
        'полина': 'Полину', 'раиса': 'Раису', 'регина': 'Регину', 'рената': 'Ренату',
        'снежана': 'Снежану', 'стелла': 'Стеллу', 'сусана': 'Сусану', 'тамара': 'Тамару',
        'эвелина': 'Эвелину', 'эльвира': 'Эльвиру', 'эмилия': 'Эмилию',
        'юлиана': 'Юлиану', 'ярослава': 'Ярославу'
    }
    
    first_lower = first_name.lower()
    if first_lower in first_name_exceptions:
        first_name_acc = first_name_exceptions[first_lower]
    elif is_female:
        if first_lower.endswith('а'):
            first_name_acc = first_name[:-1] + 'у'
        elif first_lower.endswith('я'):
            first_name_acc = first_name[:-1] + 'ю'
        elif first_lower.endswith('ь'):
            first_name_acc = first_name
        else:
            first_name_acc = first_name
    else:
        if first_lower.endswith('й'):
            first_name_acc = first_name[:-1] + 'я'
        elif first_lower.endswith('ь'):
            first_name_acc = first_name[:-1] + 'я'
        elif first_lower.endswith('а'):
            first_name_acc = first_name[:-1] + 'у'
        elif first_lower.endswith('я'):
            first_name_acc = first_name[:-1] + 'ю'
        elif first_lower.endswith('ел'):
            first_name_acc = first_name[:-2] + 'ла'
        elif first_lower.endswith('ил'):
            first_name_acc = first_name[:-2] + 'ила'
        else:
            first_name_acc = first_name + 'а'
    
    last_name_acc = _decline_lastname(last_name, is_female, 'accusative')
    
    if is_female:
        if middle_name.endswith(('на', 'вна')):
            middle_name_acc = middle_name[:-1] + 'у'
        else:
            middle_name_acc = middle_name
    else:
        if middle_name.endswith(('ич', 'ович', 'евич')):
            middle_name_acc = middle_name + 'а'
        else:
            middle_name_acc = middle_name
    
    return f"{last_name_acc} {first_name_acc} {middle_name_acc}"



def leader_to_genitive(leader):
    """Преобразование руководителя в родительный падеж (с инициалами)"""
    if not leader:
        return leader
    
    leader = str(leader).strip()
    parts = leader.split()
    
    if len(parts) < 2:
        # Только фамилия
        last_name = leader.title()
        last_lower = last_name.lower()
        is_female = (last_lower.endswith(('ова', 'ева', 'ина', 'ына', 'ая', 'яя')) or
                     (last_lower.endswith('а') and not last_lower.endswith('ко')))
        
        if _should_decline_lastname(last_lower, is_female):
            if is_female:
                if last_lower.endswith(('ова', 'ева', 'ина', 'ына')):
                    return last_name[:-1] + 'ой'
                elif last_lower.endswith(('ская', 'кая', 'ая')):
                    return last_name[:-2] + 'ой'
                elif last_lower.endswith('яя'):
                    return last_name[:-2] + 'ей'
                elif last_lower.endswith('а'):
                    return last_name[:-1] + 'ой'
                elif last_lower.endswith('я'):
                    return last_name[:-1] + 'ей'
            else:
                if last_lower.endswith(('ов', 'ев', 'ёв', 'ин', 'ын')):
                    return last_name + 'а'
                elif last_lower.endswith(('ский', 'цкий', 'кой', 'ая', 'ый', 'ой')):
                    return last_name[:-2] + 'ого'
                elif last_lower.endswith(('б', 'в', 'г', 'д', 'ж', 'з', 'к', 'л', 'м',
                                          'н', 'п', 'р', 'с', 'т', 'ф', 'х', 'ц', 'ч', 'ш', 'щ')):
                    return last_name + 'а'
                elif last_lower.endswith('чук'):
                    return last_name[:-3] + 'чука'
                elif last_lower.endswith('юк'):
                    return last_name[:-2] + 'юка'
                elif last_lower.endswith('ук'):
                    return last_name[:-2] + 'ука'
                elif last_lower.endswith('чак'):
                    return last_name[:-3] + 'чака'
                elif last_lower.endswith('як'):
                    return last_name[:-2] + 'яка'
                else:
                    return last_name + 'а'
        return last_name
    else:
        # Фамилия с инициалами
        last_name = parts[0].title()
        initials = ' '.join(parts[1:])
        last_lower = last_name.lower()
        is_female = (last_lower.endswith(('ова', 'ева', 'ина', 'ына', 'ая', 'яя')) or
                     (last_lower.endswith('а') and not last_lower.endswith('ко')))
        
        if _should_decline_lastname(last_lower, is_female):
            if is_female:
                if last_lower.endswith(('ова', 'ева', 'ина', 'ына')):
                    last_name_gen = last_name[:-1] + 'ой'
                elif last_lower.endswith(('ская', 'кая', 'ая')):
                    last_name_gen = last_name[:-2] + 'ой'
                elif last_lower.endswith('яя'):
                    last_name_gen = last_name[:-2] + 'ей'
                elif last_lower.endswith('а'):
                    last_name_gen = last_name[:-1] + 'ой'
                elif last_lower.endswith('я'):
                    last_name_gen = last_name[:-1] + 'ей'
                else:
                    last_name_gen = last_name
            else:
                if last_lower.endswith(('ов', 'ев', 'ёв', 'ин', 'ын')):
                    last_name_gen = last_name + 'а'
                elif last_lower.endswith(('ский', 'цкий', 'кой', 'ая', 'ый', 'ой')):
                    last_name_gen = last_name[:-2] + 'ого'
                elif last_lower.endswith(('б', 'в', 'г', 'д', 'ж', 'з', 'к', 'л', 'м',
                                          'н', 'п', 'р', 'с', 'т', 'ф', 'х', 'ц', 'ч', 'ш', 'щ')):
                    last_name_gen = last_name + 'а'
                elif last_lower.endswith('чук'):
                    last_name_gen = last_name[:-3] + 'чука'
                elif last_lower.endswith('юк'):
                    last_name_gen = last_name[:-2] + 'юка'
                elif last_lower.endswith('ук'):
                    last_name_gen = last_name[:-2] + 'ука'
                elif last_lower.endswith('чак'):
                    last_name_gen = last_name[:-3] + 'чака'
                elif last_lower.endswith('як'):
                    last_name_gen = last_name[:-2] + 'яка'
                else:
                    last_name_gen = last_name + 'а'
        else:
            last_name_gen = last_name
        
        return f"{last_name_gen} {initials}"



def reverse_initials(name):
    """Преобразование ФИО в формат 'Имя Фамилия' для подписи"""
    if not name:
        return ""
    parts = str(normalize_fio(name)).split()
    if len(parts) >= 2:
        return f"{parts[1]} {parts[0]}"
    return ' '.join(parts)


def create_safe_filename(name, protocol_type, row_num):
    """Создание безопасного имени файла"""
    if not name:
        return f"{protocol_type}_строка_{row_num}_протокол.docx"
    
    fio_normalized = normalize_fio(name)
    safe_name = re.sub(r'[<>:"/\\|?*]', '', fio_normalized)
    safe_name = safe_name.replace(' ', '_')
    filename = f"{protocol_type}_{safe_name}_{row_num}_протокол.docx"
    
    max_length = 100
    if len(filename) > max_length:
        filename = filename[:max_length] + ".docx"
    
    return filename


def create_archive(temp_dir, archive_name="протоколы_ГЭК"):
    """Создает ZIP-архив из всех файлов во временной папке"""
    current_date = datetime.now().strftime("%Y%m%d_%H%M")
    archive_filename = f"{archive_name}_{current_date}.zip"
    
    with zipfile.ZipFile(archive_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    return archive_filename


def get_last_row(sheet):
    """Определение последней заполненной строки в листе Excel"""
    max_row = sheet.max_row
    for row in range(max_row, 0, -1):
        if sheet.cell(row=row, column=1).value is not None:
            return row
    return 0