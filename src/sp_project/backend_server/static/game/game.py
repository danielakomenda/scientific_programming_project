import contextlib
import typing
import asyncio
from types import SimpleNamespace

import numpy as np

# pyscript/pyodide imports
import pyscript
import pyodide.ffi
import js

# represents pyodide's wrapping of `https://developer.mozilla.org/en-US/docs/Web/API/ImageBitmap`
ImageBitmap: typing.TypeAlias = pyodide.ffi.JsProxy


async def _load_image_bitmap_from_url(url: str):
    try:
        # fetch image from server by creating an <img> element not attached to the DOM
        done = asyncio.Event()

        def onload(this):
            done.set()

        img = js.Image.new()  # new Java-Script-Object
        img.onload = onload
        img.src = url
        await done.wait()  # wait until done.set() is called

        # convert to ImageBitmap
        res = await js.createImageBitmap(img)  # Java-Script-Function

        print(f"Loaded {url}")
        return res
    except Exception as ex:
        print(f"Exception trying to load {url} as ImageBitmap: {ex!r}")
        raise


class GameAssets:
    character: ImageBitmap
    mountain: ImageBitmap
    thunderbolt: ImageBitmap

    def __init__(
        self,
        **assets,
    ):
        for k, v in assets.items():
            setattr(self, k, v)

    @classmethod
    async def load_from_url(cls, **asset_urls):
        # simultaneously fetch all images
        async with asyncio.TaskGroup() as tg:
            fetch_tasks = {
                k: tg.create_task(_load_image_bitmap_from_url(v))
                for k, v in asset_urls.items()
            }
        # now, all fetch tasks have completed, we can access their results
        return cls(**{k: v.result() for k, v in fetch_tasks.items()})


class Rect:
    """Represents the Coordinates of an axis-aligned Rectangle"""

    def __init__(self, *, width: int, height: int, **pos_args):
        self.size = np.array((width, height), float)
        self.half_size = self.size / 2
        self._top_left_pos = np.zeros(2, float)
        for k, v in pos_args.items():
            setattr(self, k, v)

    @property
    def width(self):
        return self.size[0]

    @property
    def height(self):
        return self.size[1]

    top = property(
        lambda self: self._top_left_pos[1],
        lambda self, v: self._top_left_pos.__setitem__(1, v),
    )

    left = property(
        lambda self: self._top_left_pos[0],
        lambda self, v: self._top_left_pos.__setitem__(0, v),
    )

    bottom = property(
        lambda self: self._top_left_pos[1] + self.size[1],
        lambda self, v: self._top_left_pos.__setitem__(1, v - self.size[1]),
    )

    right = property(
        lambda self: self._top_left_pos[0] + self.size[0],
        lambda self, v: self._top_left_pos.__setitem__(0, v - self.size[0]),
    )

    hcenter = property(
        lambda self: self._top_left_pos[0] + self.half_size[0],
        lambda self, v: self._top_left_pos.__setitem__(0, v - self.half_size[0]),
    )

    def collides_with(self, other: typing.Self) -> bool:
        """Returns True if two Rectangles overlap"""

        if self.left >= other.right:
            return False
        if self.right <= other.left:
            return False
        if self.top >= other.bottom:
            return False
        if self.bottom <= other.top:
            return False
        return True


class Sprite(Rect):
    """Picture with its Position -> Represents the Rectangle, where the Picture can be found"""

    def __init__(self, image: ImageBitmap, **pos_args):
        super().__init__(width=image.width, height=image.height, **pos_args)
        self.image = image

    def draw(self, drawing_context):
        drawing_context.drawImage(self.image, int(round(self.left)), int(round(self.top)))  # JS-Canvas2D-Methode


class GameRunner:
    # the GUI elements
    info: pyscript.Element
    canvas: pyscript.Element
    assets: GameAssets

    # the game state (inititalised within `self.reset()`)
    frame: Rect
    background: Sprite
    character: Sprite
    thunderbolts: set[Sprite]
    pressed_keys: set[str]
    score: int
    game_over: bool

    def __init__(
        self, *, info: pyscript.Element, canvas: pyscript.Element, assets: GameAssets
    ):
        self.info = info
        self.canvas = canvas
        self.assets = assets

    def setup(self):
        frame_size = SimpleNamespace(width=800, height=600)

        # Represents `<canvas>`-html-dom-Object and set size
        ce = self.canvas.element
        ce.setAttribute("width", frame_size.width)
        ce.setAttribute("height", frame_size.height)

        self.frame = Rect(**vars(frame_size), top=0, left=0)

        self.background = Sprite(
            self.assets.mountain, top=self.frame.top, hcenter=self.frame.hcenter
        )

    def reset(self):
        self.character = Sprite(
            self.assets.character,
            bottom=self.frame.bottom,
            hcenter=self.frame.hcenter,
        )
        self.thunderbolts = set()
        self.score = 0
        self.level = 1
        self.game_over = False
        self.pressed_keys = set()

    @contextlib.contextmanager
    def _with_keydown_handler(self):
        """Context manager that attaches an event listener for the `keydown` event to the main body element,
        and ensures that the event listener is removed at the end again."""
        keydown_proxy = pyodide.ffi.create_proxy(self._on_keydown, capture_this=True)
        keyup_proxy = pyodide.ffi.create_proxy(self._on_keyup, capture_this=True)
        try:
            js.document.body.addEventListener("keydown", keydown_proxy)
            js.document.body.addEventListener("keyup", keyup_proxy)
            # at this point, the body of the `with` statement executes
            yield
        finally:
            js.document.body.removeEventListener("keyup", keyup_proxy)
            js.document.body.removeEventListener("keydown", keydown_proxy)
            keyup_proxy.destroy()
            keydown_proxy.destroy()

    def _on_keydown(self, this, event):
        self.pressed_keys.add(event.key)

    def _on_keyup(self, this, event):
        self.pressed_keys.remove(event.key)

    async def play_one_game(self):
        # pixels per second
        character_speed = 150
        thunderbolt_speed = 150
        # number of thunderbolts per second at level 1
        base_rate = 2

        self.reset()

        context = self.canvas.element.getContext("2d")
        self.background.draw(context)
        self.character.draw(context)
        del context

        for t in range(3, 0, -1):
            self.info.write(f"Game starts in {t} seconds")
            await asyncio.sleep(1)

        self.info.write("Score: 0")
        prev = js.Date.now()/1000
        with self._with_keydown_handler():
            while not self.game_over:
                # measure time since last tick
                now = js.Date.now()/1000
                dt = min(0.1, now - prev)
                prev = now

                self.level = 1 + int(np.sqrt(self.score / 10))

                # Generate new thunderbolts
                n_new = np.random.poisson(dt*(1 + self.level/3)*base_rate)
                n_new = max(n_new, 3 - len(self.thunderbolts))
                for _ in range(n_new):
                    thunderbolt_x = np.random.randint(
                        self.frame.left,
                        self.frame.right - self.assets.thunderbolt.width,
                    )
                    sprite = Sprite(
                        self.assets.thunderbolt, left=thunderbolt_x, top=self.frame.top
                    )
                    self.thunderbolts.add(sprite)

                # update character position
                if "ArrowLeft" in self.pressed_keys:
                    if self.character.left > self.frame.left:
                        self.character.hcenter -= character_speed * dt
                if "ArrowRight" in self.pressed_keys:
                    if self.character.right < self.frame.right:
                        self.character.hcenter += character_speed * dt

                # Update thunderbolt positions
                score = self.score
                for thunderbolt in list(self.thunderbolts):
                    thunderbolt.top += thunderbolt_speed * dt

                    # Check if thunderbolt hits the character
                    if thunderbolt.collides_with(self.character):
                        self.game_over = True

                    # Check if thunderbolt is missed
                    elif thunderbolt.bottom >= self.frame.bottom:
                        self.thunderbolts.remove(thunderbolt)
                        score += self.level
                if score != self.score:
                    self.info.write(f"Score: {score} (Level: {self.level})")
                    self.score = score

                # Draw new game state to canvas
                context = self.canvas.element.getContext("2d")
                self.background.draw(context)
                for thunderbolt in self.thunderbolts:
                    thunderbolt.draw(context)
                self.character.draw(context)
                del context

                # wait for next tick
                now = js.Date.now()/1000
                t_sleep = max(0.01, prev + 1 / 60 - now)
                await asyncio.sleep(t_sleep)

            print(f"Game finished with a score of {self.score}")
            self.info.write(f"Game Over! Score: {self.score}")

            await asyncio.sleep(1.5)
