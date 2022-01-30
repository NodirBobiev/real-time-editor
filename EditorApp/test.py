from pygame import (Color, Rect, Surface, display, draw, font, event, time, key, quit, QUIT, KEYDOWN, K_LEFT, K_RIGHT)
from random import randint
import requests

font.init()

class DisplayAble:
    def update(self, time_passed):
        pass

    def display(self):
        screen = display.get_surface()
        if screen:
            self.show(screen)

    def show(self, screen):
        pass
    

class Box(DisplayAble):
    def __init__(self, rect: Rect, background: Color, *args):
        super().__init__(*args)
        self.background = background
        self.rect = rect
    
    def show(self, screen):
        draw.rect(screen, self.background, self.rect)


class Text:
    def __init__(self, content=""):
        self.content = content
    
    def size(self):
        return len(self.content)

    def add_text(self, text:str, index=None):
        if index is None or index >= len(self.content):
            self.content += text
        else:
            self.content = self.content[:index] + text + self.content[index:]
    
    def clear_all(self):
        self.content = ""
    
    def delete_text(self, start:int, finish:int):
        if start > finish or start >= len(self.content) or finish < 0:
            return ""
        res = self.content[start: finish+1]
        self.content = self.content[:start] + self.content[finish+1:]
        return res

    def right_delete(self, index:int, delta:int):
        return self.delete_text(index, index+delta-1)
    
    def left_delete(self, index:int, delta:int):
        return self.delete_text(index-delta+1, index)
    
    def pop(self, delta:int=0):
        if delta == 0:
            return self.left_delete(len(self.content)-1, 1)
        return self.left_delete(len(self.content)-1, delta)
        
    def get_lines(self):
        lines=[]
        last = 0
        for i in range(len(self.content)):
            if self.content[i] == '\n':
                lines.append(self.content[last:i])
                last = i + 1
        lines.append(self.content[last:])
        return lines

    def get_pos(self, pos:int):
        line, last = 0, 0
        for i in range(pos):
            if self.content[i] =='\n':
                line += 1
                last = i + 1
        return (line, pos-last)


class TextField(Box, Text):
    def __init__(self, color:Color = Color(0,0,0), font=font.Font('fonts/FiraMono-Regular.ttf', 20), **kwargs):
        super().__init__(**kwargs)
        self.font = font
        self.color = color
 
    def get_pos(self, pos:int):
        loc = super().get_pos(pos)
        return (self.rect.x + self.font.size(self.content[pos-loc[1]:pos])[0],
                self.rect.y + loc[0] * self.font.get_linesize())
        

    def show(self, screen:Surface):
        super().show(screen)
        line_height = self.font.get_linesize()
        lines = self.get_lines()
        y = 0
        for line in lines:
            line_surf = self.font.render(line, True, self.color, self.background)
            screen.blit(line_surf, (self.rect.x, self.rect.y+y))
            y += line_height


class Cursor(DisplayAble):
    def __init__(self, pos:int=0, color:Color=Color(0,0,0), width:int=2, rect=None):
        self.pos = pos
        self.color = color
        self.rect = rect
        self.width = width
        self.manager = None
        self.rest_time = 0
        self.history = []

    def __str__(self):
        return f"Cusor(pos={self.pos}, rect={self.rect})"

    def deletion(self):
        if self.manager:
            self.manager.deletion(self.pos, 1, self)
            self.history.append({'type':'DELETE', 'index':self.pos})
    
    def addition(self, txt):
        if self.manager:
            self.manager.addition(self.pos, 1, self)
            self.history.append({'type':'ADD', 'index':self.pos, 'text': txt})

    def has_done(self):
        return len(self.history) > 0

    def get_oldest(self):
        return self.history[0]

    def pop_oldest(self):
        return self.history.pop(0)

    def clear_history(self):
        self.history = []

    def move(self, delta:int):
        self.rest_time = 0
        self.pos += delta

    def show(self, screen:Surface):
        draw.rect(screen, self.color, self.rect)

    def update(self, time_passed):
        self.rest_time += time_passed
    
    def display(self):
        if self.rest_time // 400 % 2 == 0:
            super().display()

class CursorsManager:
    def __init__(self):
        self.cursors = []

    def deletion(self, pos:int, delta:int, cursor:Cursor = None):
        if pos == 0:
            return
        for csr in self.cursors:
            if csr.pos > pos - delta:
                csr.pos -= min(delta, csr.pos - (pos - delta))

    def addition(self, pos:int, delta:int, cursor:Cursor = None):
        for csr in self.cursors:
            if csr.pos >= pos:
                csr.pos += delta

    def add_cursor(self, cursor:Cursor):
        if cursor not in self.cursors:
            self.cursors.append(cursor)
            cursor.manager = self
        return self.cursors.index(cursor)
    
    def delete_cursor(self, cursor:Cursor):
        if cursor in self.cursors:
            self.cursors.remove(cursor)
            return True
        return False
    
    def normalize(self, field:TextField):
        for cursor in self.cursors:
            cursor.pos = max(0, cursor.pos)
            cursor.pos = min(cursor.pos, field.size())
            loc = field.get_pos(cursor.pos)
            cursor.rect = Rect(loc[0], loc[1], cursor.width,  field.font.get_linesize())
            # cursor.rect.topright = loc
            
    def display_cursors(self):
        for cursor in self.cursors:
            cursor.display()

    def update_cursors(self, time_passed:int):
        for cursor in self.cursors:
            cursor.update(time_passed)    


class EditableTextField(TextField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = CursorsManager()

    def display(self):
        super().display()
        self.manager.normalize(self)
        self.manager.display_cursors()

    def update(self, time_passed):
        self.manager.update_cursors(time_passed)


def random_color():
    return Color(randint(0, 255),randint(0, 255),randint(0, 255))

def operate_op(op, txt):
    if op['type'] == 'ADD':
        txt.add_text(op['text'], op['index'])
        return True
    elif op['type'] == 'DELETE':
        txt.left_delete(op['index']-1, 1)
        return True
    return False

display.set_mode([700, 800])
display.set_caption('Collaborative Editor')
key.set_repeat(300, 25)
send_op_url = 'http://127.0.0.1:5000/send/op'
send_timeout = 0.01
get_url = 'http://127.0.0.1:5000/get/newops'
get_delay = 3000
last_get_time = 0
get_timeout = 5

last_rev = -1
last_txt = Text()
clock = time.Clock()
app_time = 0
running = True


field_background = Color(255,255,255)
field_rect = Rect(20, 20, 660, 760)

field = EditableTextField(rect = field_rect, background = field_background)
# field.add_text('''Hello i am going to show how to learn coding in python in a few second. Subscribe on by channel, and like my videos''')


main_cursor = Cursor(pos=0)
field.manager.add_cursor(main_cursor)

# for i in range(5):
#     field.manager.add_cursor(Cursor(pos=randint(0, 20), color = random_color()))

ignore_keys = ['left shift', 'right shift', 'left ctrl', 'right ctrl', 'left alt', 'right alt']
for i, val in enumerate(ignore_keys):
    # print( val)
    ignore_keys[i] = key.key_code(val)


while running:
    time_passed = clock.tick(40)
    # print("time_passed=",time_passed)
    app_time += time_passed
    max_send_request= 3
    while main_cursor.has_done() and max_send_request > 0:
        max_send_request -= 1
        try:
            op = main_cursor.get_oldest()
            op['last_rev'] = last_rev
            op['user'] = "Nodir"
            r = requests.post(url=send_op_url, data = op, timeout=send_timeout)
            main_cursor.pop_oldest()
            # print( r.json() )
        except:
            max_send_request = 0
            pass
    if app_time - last_get_time >= get_delay:
        print(app_time, last_get_time, get_delay)
        print( "'", last_txt.content, "'" )
        r = requests.post(url=get_url, data={'last_rev': last_rev})
        for _,  op in r.json().items():
            op['index'] = int(op['index'])
            op['review'] = int(op['review'])
            op['last_rev'] = int(op['last_rev'])
            print( op )
            last_rev = max(last_rev, op['review'])
            operate_op(op, last_txt)
        last_get_time = app_time
        field.content = last_txt.content
    
    field.update(time_passed)
    for e in event.get():
        if e.type == QUIT:
            running = False
        if e.type == KEYDOWN:
            if e.key == key.key_code('left'):
                main_cursor.move(-1)
            elif e.key == key.key_code('right'):
                main_cursor.move(+1)
            elif e.key == key.key_code('return'):
                field.add_text('\n', main_cursor.pos)
                main_cursor.addition('\n')
            elif e.key == key.key_code('backspace'):
                field.left_delete(main_cursor.pos-1, 1)
                main_cursor.deletion()
            elif e.key in ignore_keys:
                pass
            else:
                field.add_text(e.unicode, main_cursor.pos)
                main_cursor.addition(e.unicode)
    display.get_surface().fill([200,200,200])
    field.display()
    # print(field.manager.cursors)
    display.update()

quit()