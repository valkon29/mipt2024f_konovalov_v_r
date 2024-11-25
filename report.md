# Отчёт по аугментатору

Ссылка на репозиторий: [https://github.com/valkon29/mipt2024f_konovalov_v_r](https://github.com/valkon29/mipt2024f_konovalov_v_r)

Автор: Коновалов Валентин

## Input/Output
Вход:

- набор изображений
- файл с разметкой, полученной с помощью [VGG Image Annotator](https://annotate.officialstatistics.org/). Для каждой картинки она представляет из себя набор точек, которые обозначают полигон вокруг штрих-кода. Помимо этого в атрибутах прусутствует тип кода и метка валидности (за подробностями см. пример в репозитории).

Выход:

- набор изображений, полученных из входных путём некоторых искажений
- разметка в том же формате, что и на входе

## API

Исполняемый файл _main.py_, ему на вход подаются путь к папке с изображениями, путь к файлу и число, задающее кол-во изображений, которое необходимо получить из каждого исходного посредством аугментации:

```
python3 main.py images via_project_9Nov2024_20h28m_.json 2
```

Полученные изображения будут сохранены в папку _augmented images_, а разметка в файл _augmented_markup.json_. Формат выходной разметки совпадет со входным.

Сама операция искажения, применяемая к входным изображениям, захардкожена внутри файла _main.py_. В будущем планируется в какой-то степени перенести список искажений и их параметров в какой-нибудь конфиг.

## Искажения

Все искажения изображений осуществляются посредством библиотеки [albumentations](https://albumentations.ai/docs/). Она поддерживает работу с ключевыми точками, масками и bounding_box-ами, поэтому пока что её функционала вполне достаточно. Вот пример нескольких искажений, с визуализацией разметки, которые кажутся наиболее актуальными, и которые были опробованы на практике.

- __RandomCrop__: кадрирование изображение случайным образом

<div class='container'>
    <img src="visualizations/crop_input.png" alt="drawing" width="300"/>
    <img src="visualizations/crop_output.png" alt="drawing" width="300"/>
</div>

- __Rotate__: поворот на угол от 0 до 360 градусов;

<div class='container'>
    <img src="visualizations/rotate_input.png" alt="drawing" width="300"/>
    <img src="visualizations/rotate_output.png" alt="drawing" width="300"/>
</div>

- __Perspective__: углы изображения смещаются на случайные расстояния в заданных пределах, изображение деформируется соотвествующим образом

<div class='container'>
    <img src="visualizations/perspective_input.png" alt="drawing" width="300"/>
    <img src="visualizations/perspective_output.png" alt="drawing" width="300"/>
</div>

- __ISONoise__: симуляция шума, возникающего при высоких значениях ISO

<div class='container'>
    <img src="visualizations/iso_noise_input.png" alt="drawing" width="300"/>
    <img src="visualizations/iso_noise_output.png" alt="drawing" width="300"/>
</div>

- __GaussNoise__: шум из нормального распределения, применяется отдельно для каждого пикселя и для каждого канала (хотя это можно настроить)

<div class='container'>
    <img src="visualizations/gauss_noise_input.png" alt="drawing" width="300"/>
    <img src="visualizations/gauss_noise_output.png" alt="drawing" width="300"/>
</div>

- __ChromaticAberration__: симуляция хроматических аббераций изображения

<div class='container'>
    <img src="visualizations/chromatic_input.png" alt="drawing" width="300"/>
    <img src="visualizations/chromatic_output.png" alt="drawing" width="300"/>
</div>

- __GaussianBlur__: свёртка с гауссовским ядром

<div class='container'>
    <img src="visualizations/gauss_blur_input.png" alt="drawing" width="300"/>
    <img src="visualizations/gauss_blur_output.png" alt="drawing" width="300"/>
</div>

- __MotionBlur__: свёртка с продольным ядром, направление "движения" при этом выбирается случайно

<div class='container'>
    <img src="visualizations/motion_input.png" alt="drawing" width="300"/>
    <img src="visualizations/motion_output.png" alt="drawing" width="300"/>
</div>


Кроме того, была создана [таблица](https://docs.google.com/spreadsheets/d/1PcWqvZCe95tcm1lzSWeyEqdJK_wRV9SHoov22B2F4M4/edit?gid=0#gid=0) со всеми искажениями, которые потенциально нам могут пригодиться.
В столбцах присутствуют оценка релевантности отдельных искажений для нашей задачи по 10-бальной шкале, а также местами их краткое описание и допустимые границы параметров. _По многим из них пока есть сомнения, таблица заполнена не полностью_.

Столбец _limits depend on image_ для отдельных искажений даёт информмацию о том, зависят ли допустимые границы искажения от конкреного фото. К примеру, из вышеупомянутых, границы Perspective или Rotate от изображения особо не зависят, в то время как у GaussianBlur и MotionBlur эта зависмость очень явная, чем качетсвеннее было исходное фото, тем сильнее его потом можно размывать. И что делать с такими искажениями, на данный момент, скорее неясно.

## Некоторые детали
- На данный момент, если при искажении, хоть одна точка разметки кода выходит за границы полученного изображения, код считается не валидным и в разметке это отражается. В дальнейшем можно сделать умнее
- Можно задавать композицию из произвольного числа искажений, при этом задавая вероятности каждого из них. По умолчанию они применяются с вероятностью 0.5
- При всех искажениях, которые нарушают "прямоугольность" картинки, всё лишнее обрезалось. Из вышеупомянутых к таковым относятся Rotate и Perspective. Потенциально образовавшиеся области можно, например, заполнять зеркально отражённым содержанием исходной картинки

## Зависимости
Исключительно питоновские библиотеки, которые можно установить, например, с помощью утилиты PyPI:
- OpenCV
- albumentations
