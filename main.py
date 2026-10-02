# -*- coding: utf-8 -*-
"""
Simulador de Movimento CNC - versao Android (Kivy)

Port do simulador original em Tkinter para Kivy, para que possa ser
empacotado em um APK com o Buildozer e rodar em celulares/tablets Android.

Mantem:
- Coordenadas de maquina X (vertical) e Z (horizontal) em mm.
- Entrada manual de pontos com raio (interpolacao circular - G2/G3).
- Desenho de arco calculado em COORDENADAS DE MAQUINA e convertido para
  pixels so no final (correcao do bug de mistura de unidades mm x pixel).
- Padroes automaticos (Circular, Zigue-Zague, Espiral, Aleatorio, Peca CNC).
"""

import math
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Ellipse
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty

# Cores (RGBA 0..1)
BG = (0.12, 0.12, 0.12, 1)
PANEL = (0.17, 0.17, 0.17, 1)
GRID = (0.20, 0.20, 0.20, 1)
AXIS = (0.34, 0.34, 0.34, 1)
PATH = (0.0, 1.0, 0.53, 1)      # #00ff88
NODE = (1.0, 0.27, 0.27, 1)     # #ff4444
ZCOL = (1.0, 0.53, 0.0, 1)      # #ff8800
XCOL = (0.0, 1.0, 1.0, 1)       # #00ffff


class CNCCanvas(Widget):
    """Area de desenho. Guarda a geometria em coordenadas de maquina e
    redesenha tudo convertendo para pixels (resiliente a redimensionamento).
    """

    MARGIN = 44

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Limites das reguas (mm) - iguais ao programa original
        self.x_min, self.x_max = -20, 60   # X vertical
        self.z_min, self.z_max = -50, 50   # Z horizontal
        # Lista de primitivas em coordenadas de maquina
        # ('line', x1, z1, x2, z2) ou ('poly', [(x,z), ...])
        self.prims = []
        self.nodes = []  # pontos (x, z) marcados com circulo vermelho
        self.bind(size=lambda *a: self.redraw(), pos=lambda *a: self.redraw())

    # ----- conversao maquina -> pixel -----
    def to_canvas(self, x, z):
        m = self.MARGIN
        w = max(self.width, 1)
        h = max(self.height, 1)
        z_scale = (w - 2 * m) / (self.z_max - self.z_min)
        x_scale = (h - 2 * m) / (self.x_max - self.x_min)
        px = self.x + m + (z - self.z_min) * z_scale
        # Kivy tem origem embaixo-esquerda e Y cresce para cima:
        # X positivo para cima mapeia naturalmente.
        py = self.y + m + (x - self.x_min) * x_scale
        return px, py

    # ----- API de desenho (coordenadas de maquina) -----
    def add_line(self, x1, z1, x2, z2):
        self.prims.append(('line', x1, z1, x2, z2))

    def add_poly(self, pts):
        self.prims.append(('poly', pts))

    def add_node(self, x, z):
        self.nodes.append((x, z))

    def clear(self):
        self.prims = []
        self.nodes = []
        self.redraw()

    # ----- redesenho completo -----
    def redraw(self):
        self.canvas.clear()
        with self.canvas:
            Color(*BG)
            from kivy.graphics import Rectangle
            Rectangle(pos=self.pos, size=self.size)
            self._draw_grid()
            self._draw_prims()
            self._draw_nodes()

    def _draw_grid(self):
        m = self.MARGIN
        # Grade a cada 10 mm em Z e X
        Color(*GRID)
        z = int(self.z_min)
        while z <= self.z_max:
            px, _ = self.to_canvas(0, z)
            Line(points=[px, self.y + m, px, self.y + self.height - m], width=1)
            z += 10
        x = int(self.x_min)
        while x <= self.x_max:
            _, py = self.to_canvas(x, 0)
            Line(points=[self.x + m, py, self.x + self.width - m, py], width=1)
            x += 10
        # Eixos principais (x=0 e z=0)
        Color(*AXIS)
        px0, _ = self.to_canvas(0, 0)
        _, py0 = self.to_canvas(0, 0)
        Line(points=[px0, self.y + m, px0, self.y + self.height - m], width=2)
        Line(points=[self.x + m, py0, self.x + self.width - m, py0], width=2)
    def _draw_prims(self):
        Color(*PATH)
        for p in self.prims:
            if p[0] == 'line':
                _, x1, z1, x2, z2 = p
                a = self.to_canvas(x1, z1)
                b = self.to_canvas(x2, z2)
                Line(points=[a[0], a[1], b[0], b[1]], width=2)
            elif p[0] == 'poly':
                pts = p[1]
                flat = []
                for (x, z) in pts:
                    cx, cy = self.to_canvas(x, z)
                    flat += [cx, cy]
                if len(flat) >= 4:
                    Line(points=flat, width=2)

    def _draw_nodes(self):
        Color(*NODE)
        for (x, z) in self.nodes:
            cx, cy = self.to_canvas(x, z)
            Ellipse(pos=(cx - 4, cy - 4), size=(8, 8))


# ---------- geometria do arco (coordenadas de maquina) ----------
def arc_points(start_x, start_z, end_x, end_z, radius, num=60):
    """Retorna uma polilinha [(x,z), ...] aproximando o arco de raio dado
    que liga (start) a (end). Todo o calculo e em mm. Devolve None se o
    raio for pequeno demais para esses dois pontos (ai desenha-se reta).
    """
    dz = end_z - start_z
    dx = end_x - start_x
    distance = math.hypot(dz, dx)
    if distance == 0:
        return None
    if radius < distance / 2:
        return None  # raio invalido -> reta

    mid_z = (start_z + end_z) / 2
    mid_x = (start_x + end_x) / 2
    h = math.sqrt(max(0.0, radius * radius - (distance / 2) ** 2))
    perp_z = -dx / distance
    perp_x = dz / distance
    center_z = mid_z + perp_z * h
    center_x = mid_x + perp_x * h

    start_angle = math.atan2(start_x - center_x, start_z - center_z)
    end_angle = math.atan2(end_x - center_x, end_z - center_z)
    diff = end_angle - start_angle
    while diff <= -math.pi:
        diff += 2 * math.pi
    while diff > math.pi:
        diff -= 2 * math.pi

    pts = [(start_x, start_z)]
    for i in range(1, num + 1):
        t = i / num
        ang = start_angle + t * diff
        pz = center_z + radius * math.cos(ang)
        px = center_x + radius * math.sin(ang)
        pts.append((px, pz))
    return pts
# ---------- padroes automaticos ----------
def gen_circular():
    radius = 30
    for angle in range(0, 720, 5):
        rad = math.radians(angle)
        yield radius * math.sin(rad), radius * math.cos(rad)


def gen_zigzag():
    for i in range(20):
        z = -40 + i * 4
        x = 20 if i % 2 == 0 else -10
        yield x, z


def gen_spiral():
    for angle in range(0, 1080, 10):
        rad = math.radians(angle)
        r = angle / 15
        yield r * math.sin(rad), r * math.cos(rad)


def gen_random():
    for _ in range(200):
        yield random.uniform(-15, 50), random.uniform(-40, 40)


def gen_cnc_part():
    profile = [
        (0, 0), (10, 0), (10, 15), (20, 15), (20, 30),
        (35, 30), (35, 45), (20, 45), (20, 55), (0, 55), (0, 0),
    ]
    for x, z in profile:
        yield x - 10, z - 25


PATTERNS = {
    'Circular': gen_circular,
    'Zigue-Zague': gen_zigzag,
    'Espiral': gen_spiral,
    'Aleatorio': gen_random,
    'Peca CNC': gen_cnc_part,
}
# ---------- aplicativo ----------
def styled_input(hint):
    ti = TextInput(hint_text=hint, multiline=False, input_filter='float',
                   size_hint_y=None, height='44dp', foreground_color=(1, 1, 1, 1),
                   background_color=(0.12, 0.12, 0.12, 1), cursor_color=(1, 1, 1, 1),
                   halign='center', font_size='16sp')
    return ti


def styled_btn(text, color):
    return Button(text=text, size_hint_y=None, height='46dp',
                  background_normal='', background_color=color,
                  color=(1, 1, 1, 1), bold=True, font_size='15sp')


class CNCApp(App):
    def build(self):
        Window.clearcolor = BG
        root = BoxLayout(orientation='vertical')

        # Area de desenho (parte de cima)
        self.cnc = CNCCanvas(size_hint_y=0.58)
        root.add_widget(self.cnc)

        # Painel de controles rolavel (parte de baixo)
        scroll = ScrollView(size_hint_y=0.42)
        panel = GridLayout(cols=1, spacing='8dp', padding='10dp', size_hint_y=None)
        panel.bind(minimum_height=panel.setter('height'))
        scroll.add_widget(panel)
        root.add_widget(scroll)

        # Posicao atual
        self.pos_lbl = Label(text='X: 0.000    Z: 0.000', size_hint_y=None,
                             height='30dp', color=XCOL, font_size='17sp', bold=True)
        panel.add_widget(self.pos_lbl)

        # Entradas X / Z / Raio
        self.in_x = styled_input('X (mm)')
        self.in_z = styled_input('Z (mm)')
        self.in_r = styled_input('Raio (arco) - opcional')
        panel.add_widget(self.in_x)
        panel.add_widget(self.in_z)
        panel.add_widget(self.in_r)

        add_btn = styled_btn('ADICIONAR PONTO', (0.0, 0.67, 0.33, 1))
        add_btn.bind(on_release=lambda *a: self.add_manual_point())
        panel.add_widget(add_btn)

        run_btn = styled_btn('EXECUTAR PONTOS', (0.0, 0.40, 0.67, 1))
        run_btn.bind(on_release=lambda *a: self.run_manual_points())
        panel.add_widget(run_btn)

        self.count_lbl = Label(text='Pontos inseridos: 0', size_hint_y=None,
                               height='24dp', color=(0.6, 0.6, 0.6, 1), font_size='13sp')
        panel.add_widget(self.count_lbl)

        clearp_btn = styled_btn('LIMPAR PONTOS', (0.33, 0.33, 0.33, 1))
        clearp_btn.bind(on_release=lambda *a: self.clear_manual_points())
        panel.add_widget(clearp_btn)

        # Padrao automatico
        panel.add_widget(Label(text='Padrao automatico:', size_hint_y=None,
                               height='24dp', color=(1, 1, 1, 1), font_size='14sp'))
        self.pattern = Spinner(text='Circular', values=list(PATTERNS.keys()),
                               size_hint_y=None, height='44dp')
        panel.add_widget(self.pattern)

        start_btn = styled_btn('INICIAR PADRAO', (0.0, 0.67, 0.33, 1))
        start_btn.bind(on_release=lambda *a: self.start_pattern())
        panel.add_widget(start_btn)

        stop_btn = styled_btn('PARAR', (0.67, 0.20, 0.20, 1))
        stop_btn.bind(on_release=lambda *a: self.stop())
        panel.add_widget(stop_btn)

        row = BoxLayout(size_hint_y=None, height='46dp', spacing='8dp')
        home_btn = styled_btn('VOLTAR ORIGEM', (0.33, 0.33, 0.33, 1))
        home_btn.bind(on_release=lambda *a: self.go_home())
        clearg_btn = styled_btn('LIMPAR GRAFICO', (0.33, 0.33, 0.33, 1))
        clearg_btn.bind(on_release=lambda *a: self.clear_graph())
        row.add_widget(home_btn)
        row.add_widget(clearg_btn)
        panel.add_widget(row)

        self.status = Label(text='Pronto', size_hint_y=None, height='24dp',
                            color=(0.6, 0.6, 0.6, 1), font_size='13sp')
        panel.add_widget(self.status)

        # Estado
        self.current_x = 0.0
        self.current_z = 0.0
        self.first_drawn = False
        self.manual_points = []
        self.speed = 0.08  # segundos entre pontos
        self._event = None
        return root
    # ----- logica -----
    def _parse(self, s):
        s = (s or '').strip().replace(',', '.')
        return float(s) if s else None

    def add_point(self, new_x, new_z, radius=None):
        """Desenha linha ou arco do ponto anterior ate o novo (coord. de maquina)."""
        if not self.first_drawn:
            self.first_drawn = True
        else:
            if radius:
                pts = arc_points(self.current_x, self.current_z, new_x, new_z, radius)
                if pts is None:
                    self.cnc.add_line(self.current_x, self.current_z, new_x, new_z)
                else:
                    self.cnc.add_poly(pts)
            else:
                self.cnc.add_line(self.current_x, self.current_z, new_x, new_z)

        self.cnc.add_node(new_x, new_z)
        self.current_x = new_x
        self.current_z = new_z
        self.cnc.redraw()
        self.pos_lbl.text = f'X: {new_x:.3f}    Z: {new_z:.3f}'
        self.status.text = f'X: {new_x:.3f}, Z: {new_z:.3f}'

    def add_manual_point(self):
        try:
            x = self._parse(self.in_x.text)
            z = self._parse(self.in_z.text)
            r = self._parse(self.in_r.text)
        except ValueError:
            self.status.text = 'Valores invalidos!'
            return
        if x is None and z is None:
            self.status.text = 'Digite ao menos X ou Z.'
            return
        if r is not None and r <= 0:
            self.status.text = 'O raio deve ser > 0.'
            return
        # mantem valor anterior quando o campo fica vazio
        last = self.manual_points[-1] if self.manual_points else (0.0, 0.0, None)
        if x is None:
            x = last[0]
        if z is None:
            z = last[1]
        self.manual_points.append((x, z, r))
        self.count_lbl.text = f'Pontos inseridos: {len(self.manual_points)}'
        rt = f' [R={r}]' if r else ''
        self.status.text = f'Adicionado X={x:.3f}, Z={z:.3f}{rt}'
        self.in_x.text = ''
        self.in_z.text = ''
        self.in_r.text = ''

    def run_manual_points(self):
        if not self.manual_points:
            self.status.text = 'Insira ao menos um ponto!'
            return
        self.stop()
        self.clear_graph()
        self._queue = list(self.manual_points)
        self._idx = 0
        self.status.text = 'Executando pontos...'
        self._event = Clock.schedule_interval(self._step_manual, self.speed)

    def _step_manual(self, dt):
        if self._idx >= len(self._queue):
            self.stop()
            self.status.text = 'Pontos executados!'
            return False
        x, z, r = self._queue[self._idx]
        self._idx += 1
        self.add_point(x, z, r)

    def start_pattern(self):
        self.stop()
        self.clear_graph()
        self._gen = PATTERNS[self.pattern.text]()
        self.status.text = f'Padrao: {self.pattern.text}'
        self._event = Clock.schedule_interval(self._step_pattern, self.speed)

    def _step_pattern(self, dt):
        try:
            x, z = next(self._gen)
        except StopIteration:
            self.stop()
            self.status.text = 'Concluido!'
            return False
        self.add_point(x, z)

    def stop(self):
        if self._event is not None:
            self._event.cancel()
            self._event = None
        self.status.text = 'Parado'

    def go_home(self):
        if self.current_x == 0 and self.current_z == 0:
            return
        self.add_point(0, 0)

    def clear_graph(self):
        self.cnc.clear()
        self.current_x = 0.0
        self.current_z = 0.0
        self.first_drawn = False
        self.pos_lbl.text = 'X: 0.000    Z: 0.000'
        self.status.text = 'Grafico limpo'

    def clear_manual_points(self):
        self.stop()
        self.manual_points = []
        self.count_lbl.text = 'Pontos inseridos: 0'
        self.clear_graph()
        self.status.text = 'Pontos limpos'


if __name__ == '__main__':
    CNCApp().run()
