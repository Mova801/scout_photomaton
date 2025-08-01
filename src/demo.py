from pathlib import Path
from threading import Thread
import time
import PIL
import PIL.Image
import cv2
import pygame as pg

cv2.setLogLevel(0)


class Config:
    # pins
    TOKEN_SLOT_PIN: int = 24
    BUTTON_PIN: int = 25
    # paths
    PHOTOS_FOLDER: Path = Path("photos")
    WATERMARK_IMAGE_PATH: Path = (
        Path("images") / Path("template") / Path("template.png")
    )
    BACKGROUND_IMAGE_PATH: Path = Path("images") / Path("background.png")
    ARROW_IMAGE_PATH_PATH: Path = Path("images") / Path("arrow.png")
    # font
    FONT_FAMILY: str = None
    # colors
    TEXT_COLOR: pg.Color = pg.Color("white")
    BACKGROUND_COLOR: pg.Color = pg.Color("black")
    # photobooth
    PHOTO_COUNT: int = 3
    COUNTDOWN: int = 3
    # camera
    DEFAULT_CAMERA: int = 0
    # printer
    MAX_QUEUE_SIZE: int = 3
    MAX_WAIT_TIME: int = 60
    # image
    IMAGE_WIDTH = 550
    IMAGE_HEIGHT = 360
    # other
    WIN_SCALE_FACTOR: int = 1
    TRANSITION_DELAY_SEC: float = 0.2


class PrinterJobStates:
    # Stati possibili:
    # 3 = pending (in attesa)
    # 4 = pending-held (in attesa, bloccato)
    # 5 = processing (in elaborazione)
    # 6 = processing-stopped (elaborazione fermata)
    # 7 = canceled (annullato)
    # 8 = aborted (interrotto)
    # 9 = completed (completato)
    PENDING = 3
    PENDING_HELD = 4
    PROCESSING = 5
    PROCESSING_STOPPED = 6
    CANCELED = 7
    ABORTED = 8
    COMPLETED = 9


class CannotTakePictureError(Exception):

    def __init__(self, *args):
        super().__init__(*args)


class AppManager:

    def __init__(self, debug: bool = False) -> None:
        pg.init()
        pg.mouse.set_visible(False)

        # vars
        self._debug = debug
        self._screen_size = pg.display.Info().current_w, pg.display.Info().current_h
        self._resize(Config.WIN_SCALE_FACTOR)
        self._screen = pg.display.set_mode(self._screen_size, pg.FULLSCREEN)
        self._current_pics = []
        self._images = {
            Config.BACKGROUND_IMAGE_PATH: pg.image.load(
                str(Config.BACKGROUND_IMAGE_PATH)
            ).convert(),
            Config.ARROW_IMAGE_PATH_PATH: pg.image.load(
                str(Config.ARROW_IMAGE_PATH_PATH)
            ).convert_alpha(),
        }

        self._display_image(self._images.get(Config.BACKGROUND_IMAGE_PATH))
        self._display_text("Avvio...", None, 200)
        pg.display.flip()

        # inizializzazione videocamera su un thread a parte per non blocare l'applicazione
        # Thread(target=self._init_camera).start()
        self._init_camera()

        # paths
        Config.PHOTOS_FOLDER.mkdir(exist_ok=True, parents=True)

    def _init_camera(self) -> None:
        self.camera = cv2.VideoCapture(Config.DEFAULT_CAMERA)

    def _resize(self, k) -> None:
        if not k or k == 1:
            return
        self._screen_size = tuple(s * k for s in self._screen_size)
        self._screen = pg.display.set_mode(self._screen_size)

    def _display_image(
        self,
        img: pg.Surface,
        scale: float = 1,
        cover: bool = True,
        pos: tuple[int, int] | None = None,
    ) -> None:
        scale = min(1, abs(scale))
        img_width, img_height = img.get_size()

        if cover:
            scale_x = self._screen_size[0] / img_width
            scale_y = self._screen_size[1] / img_height
            scale = min(scale_x, scale_y)

        # Nuove dimensioni
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        # Ridimensiona
        scaled_img = pg.transform.smoothscale(img, (new_width, new_height))
        # Posiziona l'immagine
        if not pos:
            pos = None, None
        x = pos[0] if pos[0] is not None else (self._screen_size[0] - new_width) // 2
        y = pos[1] if pos[1] is not None else (self._screen_size[1] - new_height) // 2
        # Mostra
        self._screen.blit(scaled_img, (x, y))

    def _display_text(
        self, text: str, pos: tuple[int, int], size, center: bool = True
    ) -> None:
        textsurf = pg.font.Font(Config.FONT_FAMILY, size).render(
            text, 1, Config.TEXT_COLOR
        )
        textpos = textsurf.get_rect()
        if center:
            textpos.centerx = self._screen.get_rect().centerx
            textpos.centery = self._screen.get_rect().centery
        else:
            textpos.centerx, textpos.centery = pos
        self._screen.blit(textsurf, textpos)

    def _query_pin_state(self, pin: int) -> None:
        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_p:
                return True
        return False

    def _check_for_close_event(self) -> bool:
        for event in pg.event.get():
            if event.type == pg.QUIT or (
                event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE
            ):
                return True
        return False

    def _wait(self, secs) -> None:
        pg.event.pump()
        pg.time.wait(int(secs * 1000))
        pg.event.pump()

    def _load_photo(self, image_path: Path) -> None:
        self._images[image_path] = pg.image.load(str(Config.PHOTOS_FOLDER / image_path))

    def _unload_photo(self, image_path: Path) -> None:
        if image_path in self._images:
            self._images.pop(image_path)

    def _generate_filename(self, prefix: str = "foto_") -> Path:
        return Path(f"{prefix}{time.strftime('%Y%m%d_%H%M%S')}.png")

    def _take_picture(self) -> None:
        result, image = self.camera.read()
        if not result:
            raise CannotTakePictureError("Impossibile scattare la foto")
        try:
            filename = self._generate_filename()
            full_path = Config.PHOTOS_FOLDER / filename
            success = cv2.imwrite(str(full_path.resolve()), image)
            if not success:
                raise CannotTakePictureError("Errore nel salvare l'immagine")
            self._current_pics.append(filename)
        except Exception as e:
            raise CannotTakePictureError(f"Errore durante il salvataggio: {e}")

    def _show_countdown(self, count: 3) -> None:
        self._display_background_alpha()
        for i in range(count, 0, -1):
            self._display_text(str(i), None, 500)
            pg.display.flip()
            self._wait(1)
            self._display_background_alpha()
        self._display_text("Mettiti in posa!", None, 200)
        pg.display.flip()

    def _display_background_alpha(self) -> None:
        self._screen.fill(Config.BACKGROUND_COLOR)
        self._display_image(self._images.get(Config.BACKGROUND_IMAGE_PATH))
        overlay = pg.Surface(self._screen.get_size())
        overlay.set_alpha(int(255 * 0.75))
        overlay.fill(Config.BACKGROUND_COLOR)
        self._screen.blit(overlay, (0, 0))

    def _add_shoot_effect(self) -> None:
        self._screen.fill(pg.Color("gray"))
        pg.display.flip()
        self._wait(0.3)
        self._screen.fill(pg.Color("white"))
        pg.display.flip()
        self._wait(0.5)

    def _merge_photoshoot(self) -> PIL.Image:
        # template in (55, 30) con IMAGE_WIDTH, IMAGE_HEIGHT (centrato)
        positions = [(625, 30), (625, 410), (55, 410)]
        pictures = [
            PIL.Image.open(Config.PHOTOS_FOLDER / picpath).resize(
                (Config.IMAGE_WIDTH, Config.IMAGE_HEIGHT)
            )
            for picpath in self._current_pics
        ]
        merge = PIL.Image.open(Config.WATERMARK_IMAGE_PATH)
        [merge.paste(pic, pos) for pic, pos in zip(pictures, positions)]
        return merge

    def _print_pic(self, pic_path: Path) -> None:
        self._wait(8)

    def _empty_directory(self, dir: Path) -> None:
        for item in dir.iterdir():
            if item.is_file() and not item.name.startswith("merge"):
                item.unlink()

    def show_start_screen(self) -> None:
        self._screen.fill(Config.BACKGROUND_COLOR)
        self._display_image(self._images.get(Config.BACKGROUND_IMAGE_PATH))
        self._display_text("Inserisci un gettone", None, 180)
        x: int = self._screen.get_rect().centerx
        y: int = self._screen.get_rect().centery + 100
        self._display_text("per continuare", (x, y), 100, False)
        pg.display.flip()

    def wait_for_request(self) -> None:
        # aspetto l'inserimento di un gettone
        wait_for_token: bool = True
        while wait_for_token:
            if self._check_for_close_event():
                return False
            wait_for_token = not self._query_pin_state(Config.TOKEN_SLOT_PIN)

        # immagine con frecce in basso verso il pulsante
        self._display_background_alpha()
        x, y = self._screen.get_rect().center
        self._display_image(
            self._images.get(Config.ARROW_IMAGE_PATH_PATH),
            0.3,
            False,
            (None, y + y // 3),
        )
        self._display_text("Premi il pulsante ", (x, y - 50), 130, False)
        self._display_text("quando sei pronto", (x, y + 50), 130, False)
        pg.display.flip()

        # aspetto la pressione del pulsante
        wait_for_button_pressed: bool = True
        while wait_for_button_pressed:
            if self._check_for_close_event():
                return False
            wait_for_button_pressed = not self._query_pin_state(Config.BUTTON_PIN)
        return True

    def start_photoshoot(self) -> None:
        for i in range(1, Config.PHOTO_COUNT + 1):
            print(f"foto {i}/{Config.PHOTO_COUNT}")
            self._display_background_alpha()
            self._display_text(f"Foto {i}/{Config.PHOTO_COUNT}", None, 300)
            pg.display.flip()
            self._wait(2)
            self._show_countdown(Config.COUNTDOWN)
            self._wait(2)
            self._take_picture()
            self._add_shoot_effect()
            self._display_background_alpha()
            pg.display.flip()
            self._wait(1)

    def print_photoshoot(self) -> None:
        # creo la foto da stampare
        pic = self._merge_photoshoot()
        pic_path = self._generate_filename("merge_")
        pic.save(Config.PHOTOS_FOLDER / pic_path)

        # mostra la foto da stampare
        self._display_background_alpha()
        self._load_photo(pic_path)
        self._display_image(self._images.get(pic_path), scale=0.5, cover=False)
        self._unload_photo(pic_path)
        self._display_text(
            "Stampa in corso...",
            (self._screen.get_rect().centerx, self._screen.get_height() - 100),
            100,
            False,
        )
        pg.display.flip()

        # stampo la foto (richiederà un po' di tempo)
        self._print_pic(pic_path)
        self._current_pics.clear()
        self._empty_directory(Config.PHOTOS_FOLDER)

        # messaggio di arrivederci
        x, y = self._screen.get_rect().center
        self._display_background_alpha()
        self._display_text("Stampa conclusa", None, 120)
        self._display_text("Alla prossima!", (x, y + 100), 100, False)
        pg.display.flip()
        self._wait(3)

    def run(self) -> None:
        try:
            while True:
                self.show_start_screen()
                if not self.wait_for_request():
                    break
                self.start_photoshoot()
                self.print_photoshoot()
        finally:
            pg.quit()


def main(debug: bool = False) -> None:
    manager: AppManager = AppManager(debug)
    manager.run()


if __name__ == "__main__":
    Thread(target=main).start()
