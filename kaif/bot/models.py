from django.db import models


class Comment(models.Model):
    date = models.CharField(max_length=50, verbose_name='Дата публикации')
    content = models.TextField(verbose_name='Комментарий')
    count_star = models.IntegerField(verbose_name='Количество звёзд')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'Комментарий {self.date}'


class TelegramUser(models.Model):
    user_id = models.IntegerField(primary_key=True, verbose_name='ID пользователя')
    username = models.CharField(max_length=150, null=True, blank=True)
    balance = models.IntegerField(default=0, verbose_name='Баланс (в руб.)')

    class Meta:
        verbose_name = 'Телеграм пользователь'
        verbose_name_plural = 'Телеграм пользователи'

    def __str__(self):
        return f'№{self.user_id} - {self.username}'


class PaymentCrypto(models.Model):
    title = models.CharField(max_length=50, verbose_name='Монета')
    code = models.CharField(max_length=5, editable=False, verbose_name='Код')
    card = models.TextField(verbose_name='Кошелёк')

    class Meta:
        verbose_name = 'Способ оплаты (криптовалюта)'
        verbose_name_plural = 'Способы оплаты (криптовалюта)'

    def __str__(self):
        return self.title


class City(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название города')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'


class Area(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название района')
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name='Город')

    class Meta:
        verbose_name = 'Район'
        verbose_name_plural = 'Районы'

    def __str__(self):
        return f'{self.name}'


class Pack(models.Model):
    weight = models.FloatField(verbose_name='Вес')
    price = models.IntegerField(verbose_name='Цена')
    areas = models.ManyToManyField(Area, verbose_name='Районы')

    class Meta:
        verbose_name = 'Фасовка'
        verbose_name_plural = 'Фасовки'

    def __str__(self):
        return f'{self.weight} г за {self.price} руб'


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название товара')
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name='Город')
    packs = models.ManyToManyField(Pack, verbose_name='Фасовки')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    photo = models.ImageField(blank=True, null=True, verbose_name='Фотография')
    pre_order = models.BooleanField(default=False, verbose_name='Предзаказ')

    def __str__(self):
        return f'{self.city} - {self.name}'

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'


class Exchange(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название обменника')
    card = models.CharField(max_length=100, verbose_name='Номер карты')
    percent = models.FloatField(verbose_name='Процент комиссии')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Обменник'
        verbose_name_plural = 'Обменники'
