from random import randint
from abc import ABC, abstractmethod
from typing import Tuple, List, Set, Optional
from pygame.color import Color

import pygame

# Константы для размеров
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
START_APPLE_POSITION = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
START_SNAKE_POSITION = (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4)


# Направления движения
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
START_SNAKE_DIRECTION = RIGHT

# Цвета фона - черный
BOARD_BACKGROUND_COLOR = (0, 0, 0)

# Скорость движения змейки
SPEED = 3


class GameObjectInternal(ABC):
    """
    База для визуальных объекто игры, которая предоставляет геометрическую
    оболочку и базовый интерфейс.
    """

    def __init__(self, surface: pygame.Surface, size: int,
                 position: Tuple[int, int] = (0, 0)):

        self._position = position
        self._surface = surface
        self._size = size

    @property
    @abstractmethod
    def body_color(self) -> Color:
        """Основной цвет объекта: getter"""
        ...

    @body_color.setter
    @abstractmethod
    def body_color(self, val: Color):
        """Основной цвет объекта: setter"""
        ...

    @abstractmethod
    def draw(self) -> None:
        """Отрисовка объекта по _position в _surface"""
        pass

    def draw_atom(self, point, color, border_color) -> None:
        """Хелпер для отрисовки одного сегмента с рамкой"""
        rect = pygame.Rect(point[0], point[1], self.size, self.size)
        pygame.draw.rect(self.surface, color, rect)
        pygame.draw.rect(self.surface, border_color, rect, 1)

    def erase_atom(self, point) -> None:
        """Хелпер для удаления сегмента"""
        rect = pygame.Rect(point[0], point[1], self.size, self.size)
        pygame.draw.rect(self.surface, BOARD_BACKGROUND_COLOR, rect)

    @property
    def position(self) -> Tuple[int, int]:
        """Положение объекта на плоскости: getter. Целочисленные x, y
        левой верхней точки
        """
        return self._position

    @property
    def surface(self) -> pygame.Surface:
        """Объект GDI для отрисовки"""
        return self._surface

    @property
    def size(self) -> int:
        """Размер объекта в пикселах"""
        return self._size


class AppleInternal(GameObjectInternal):
    """Представляет фигуру яблока."""

    BORDER_COLOR = (93, 216, 228)

    def __init__(self, surface: pygame.Surface, size: int,
                 position: Tuple[int, int]):

        super().__init__(surface, size, position)
        self._color = Color(255, 0, 0)

    @property
    def body_color(self) -> Color:
        """Цвет яблока: getter"""
        return self._color

    @body_color.setter
    def body_color(self, val: Color):
        """Цвет яблока: setter"""
        self._color = val

    def draw(self) -> None:
        """Отрисовка яблока"""
        super().draw_atom(super().position, self.body_color,
                          AppleInternal.BORDER_COLOR)

    def randomize_position(self) -> Tuple[int, int]:
        """Расположение яблока на плоскости"""
        last_pos = self._position
        while last_pos == self._position:
            x = randint(0, self.surface.get_width() - self._size)
            y = randint(0, self.surface.get_height() - self._size)
            self._position = (
                x - x % self._size,
                y - y % self._size
            )

        return self._position

    def erase(self) -> None:
        """Скрытие яблока"""
        super().erase_atom(super().position)


class SnakeInternal(GameObjectInternal):
    """Представляет удава"""

    BORDER_COLOR = (93, 216, 228)

    def __init__(self, surface: pygame.Surface, size: int,
                 position: Tuple[int, int]):

        super().__init__(surface, size, position)

        self._color = Color(0, 240, 0)
        self._color_head = Color(0, 255, 0)
        # ставится в move на удаляемый хвост
        self._last: Optional[Tuple[int, int]] = None
        self._positions: List[Tuple[int, int]] = []
        self._direction: Tuple[int, int] = START_SNAKE_DIRECTION
        self.next_direction: Optional[Tuple[int, int]] = None
        self._increase: bool = False
        # нужно, чтобы быстро определять попадание яблока в тело
        # # или головы в тело за O(1)
        self._tail_cache: Set[Tuple[int, int]] = set()

    @property
    def length(self) -> int:
        """Возвращает размер удава в сегментах"""
        return len(self._positions) + 1

    @property
    def direction(self) -> Tuple[int, int]:
        """Возвращает текущее направление движения удава"""
        return self._direction

    @property
    def body_color(self) -> Color:
        """Возвращает цвет удава"""
        return self._color

    @body_color.setter
    def body_color(self, val: Color):
        """Устанавливает цвет удава"""
        self._color = val

    def update_direction(self, next_direction):
        """Меняет направление движения удава"""
        self.next_direction = next_direction

    def move(self) -> bool:
        """Выполняет шаг перемещения удава"""
        self._direction = (self._direction
                           if self.next_direction
                           is None else self.next_direction)
        self.next_direction = None

        if self._increase is False:
            if len(self._positions) > 0:
                # хвост, который будет удалён при перерисовке (_erase_last)
                self._last = self._positions.pop()
                self._tail_cache.remove(self._last)
                self._positions.insert(0, super().position)
                self._tail_cache.add(super().position)
            else:
                # хвост, который будет удалён при перерисовке (_erase_last)
                self._last = self.position
        else:
            self._positions.insert(0, super().position)
            self._tail_cache.add(super().position)
            self._increase = False

        self._position = self._get_next_head()

        return self.is_point_in_snake(self._position)

    def is_point_in_snake(self, point: Tuple[int, int]) -> bool:
        """Проверяет попадание точки в тело удава"""
        return point in self._tail_cache

    def increase(self):
        """Помечает удава, как готового к росту на 1 сегмент при
        следующем move
        """
        self._increase = True

    def draw(self) -> None:
        """Отображает удава на двумерной плоскости"""
        super().draw_atom(super().position, self.body_color,
                          SnakeInternal.BORDER_COLOR)

        for position in self._positions[::-1]:
            super().draw_atom(position, self.body_color,
                              SnakeInternal.BORDER_COLOR)

        self._erase_last()

    def get_head_position(self):
        """Возвращает голову удава"""
        return self.position

    def reset(self):
        """Сбрасывает удава в начальное состояние"""
        self._erase_last()
        for pt in self._positions:
            super().erase_atom(pt)
        super().erase_atom(super().position)

        self._positions = []
        self._direction = START_SNAKE_DIRECTION
        self.next_direction = None
        self._tail_cache.clear()

    def _get_next_head(self) -> Tuple[int, int]:
        """Вычисляет координаты следующей готовы удава при шаге перемещения"""
        x = super().position[0] + self._direction[0] * self.size
        y = super().position[1] + self._direction[1] * self.size
        if (x < 0):
            x = SCREEN_WIDTH - self.size
        if (x > SCREEN_WIDTH - self.size):
            x = 0
        if (y < 0):
            y = SCREEN_HEIGHT - self.size
        if (y > SCREEN_HEIGHT - self.size):
            y = 0

        return (x, y)

    def _erase_last(self):
        """Скрывает остаток хвоста удава"""
        if self._last is not None:  # затирание last
            super().erase_atom(self._last)
            self._last = None


# Тут опишите все классы игры
class GameController:
    """Представляет логику игры"""

    def __init__(self, game_object, snake, apple):
        self.snake = snake
        self.apple = apple
        self.game_object = game_object

    def handle_keys(self) -> bool:
        """
        Тут процессится нажатая клавиша-стрелка и событие завершения игры

        Returns: True, если нажата клавиша и False, если был сигнал выхода
            из игры.
        """
        for event in self.game_object.event.get():
            if event.type == self.game_object.QUIT:
                return False

            if event.type == self.game_object.KEYDOWN:
                if (event.key == self.game_object.K_UP
                        and self.snake.direction != DOWN):

                    self.snake.update_direction(UP)

                elif (event.key == self.game_object.K_DOWN
                      and self.snake.direction != UP):

                    self.snake.update_direction(DOWN)

                elif (event.key == self.game_object.K_LEFT
                      and self.snake.direction != RIGHT):

                    self.snake.update_direction(LEFT)

                elif (event.key == self.game_object.K_RIGHT
                      and self.snake.direction != LEFT):

                    self.snake.update_direction(RIGHT)
        return True

    def validate_snake_head(self) -> None:
        """Тут проверяем не съел ли удав яблоко, и если съел, то удлиняем"""
        if self.snake.get_head_position() == self.apple.position:
            # питон съел яблоко
            self.snake.increase()
            self.apple.erase()
            self.randomize_apple()

    def randomize_apple(self) -> None:
        """Кидает яблоко на плоскость"""
        while True:
            point = self.apple.randomize_position()
            # яблоко не должно попасть на питона
            if not self.snake.is_point_in_snake(point):
                break


# Инициализация PyGame
pygame.init()

# Настройка игрового окна
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)

# Заголовок окна игрового поля
pygame.display.set_caption('Змейка')

# Настройка времени
clock = pygame.time.Clock()


def main():
    """Точка входа игры"""
    apple = AppleInternal(screen, GRID_SIZE, START_APPLE_POSITION)
    snake = SnakeInternal(screen, GRID_SIZE, START_SNAKE_POSITION)
    controller = GameController(pygame, snake, apple)

    apple.draw()
    snake.draw()
    pygame.display.update()

    while True:
        clock.tick(SPEED)
        if not controller.handle_keys():
            break
        if snake.move():
            # произошло пересечение головы с телом питона
            snake.reset()
            apple.erase()
            controller.randomize_apple()
        else:
            # проверяем съедание яблока
            controller.validate_snake_head()
        apple.draw()
        snake.draw()
        pygame.display.update()

    pygame.quit()


class FakeSurfake:
    """Мок GDI для тестирования"""

    pass


class GameObject(GameObjectInternal):
    """Mock for tests"""

    def __init__(self):
        super().__init__(object(), 20, (40, 40))

    @property
    def body_color(self) -> Color:
        """Цвет яблока: getter"""
        return Color(0, 0, 0)

    @body_color.setter
    def body_color(self, val: Color):
        """Цвет яблока: setter"""
        pass

    def draw(self) -> None:
        """Mock"""
        pass


class Apple(GameObject, AppleInternal):
    """Мок для тестов"""

    def __init__(self):
        super(AppleInternal, self).__init__(object(), 20, (50, 50))


class Snake(GameObject, SnakeInternal):
    """Мок для тестов"""

    def __init__(self):
        super(SnakeInternal, self).__init__(object(), 20, (50, 50))

    @property
    def positions(self):
        """Мок для тестов"""
        pass

    @property
    def length(self):
        """Мок для тестов"""
        pass

    @property
    def direction(self):
        """Мок для тестов"""
        pass


def handle_keys():
    """Мок для тестов"""
    pass


if __name__ == '__main__':
    main()
