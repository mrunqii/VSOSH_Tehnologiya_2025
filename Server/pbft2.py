class PBFT:
    def __init__(self, nodes, node_id):
        self.nodes = nodes          # Список всех узлов в сети
        self.node_id = node_id      # Идентификатор этого узла
        self.requests = []          # Очередь запросов от клиентов
        self.sequence_number = 0    # Текущий порядковый номер
        self.log = {}               # Журнал всех запросов и их состояний
        self.view = 0               # Текущий номер представления (view)
        self.primary = 0            # ID первичного узла (меняется с view)
        
        # Буферы сообщений
        self.pre_prepare_msgs = {}
        self.prepare_msgs = {}
        self.commit_msgs = {}

    def request(self, data):
        """Клиент делает запрос к системе"""
        request_id = f"req-{len(self.requests)}"
        self.requests.append((request_id, data))
        
        if self.is_primary():
            # Первичный узел запускает протокол PBFT
            self.start_pbft(request_id, data)
        else:
            # Пересылаем запрос первичному узлу
            primary_node = self.nodes[self.primary]
            primary_node.receive(('request', request_id, data, self.node_id))

    def is_primary(self):
        """Проверяет, является ли этот узел первичным для текущего view"""
        return self.node_id == self.primary

    def start_pbft(self, request_id, data):
        """Первичный узел инициирует протокол PBFT"""
        self.sequence_number += 1
        self.log[request_id] = {
            'sequence': self.sequence_number,
            'data': data,
            'state': 'pre-prepare',
            'prepares': set(),    # Множество узлов, отправивших prepare
            'commits': set()      # Множество узлов, отправивших commit
        }
        
        # Создаем и рассылаем pre-prepare сообщение
        msg = ('pre-prepare', request_id, self.view, self.sequence_number, data)
        self.log[request_id]['pre-prepare'] = msg
        self.broadcast(msg)

    def broadcast(self, msg):
        """Отправляет сообщение всем узлам (включая себя)"""
        for node in self.nodes:
            node.receive(msg)

    def receive(self, msg):
        """Обрабатывает входящие сообщения"""
        msg_type = msg[0]
        
        if msg_type == 'request':
            # Только первичный узел обрабатывает запросы клиентов напрямую
            _, request_id, data, client_id = msg
            if self.is_primary():
                self.start_pbft(request_id, data)
                
        elif msg_type == 'pre-prepare':
            self.handle_pre_prepare(msg)
            
        elif msg_type == 'prepare':
            self.handle_prepare(msg)
            
        elif msg_type == 'commit':
            self.handle_commit(msg)
            
        elif msg_type == 'view-change':
            # Обработка смены представления (упрощенная)
            pass

    def handle_pre_prepare(self, msg):
        """Обрабатывает pre-prepare сообщение от первичного узла"""
        _, request_id, view, seq, data = msg
        
        # Проверяем сообщение
        if (view != self.view or 
            not self.is_primary() or 
            seq <= self.sequence_number):
            return
            
        # Сохраняем pre-prepare сообщение
        if request_id not in self.log:
            self.log[request_id] = {
                'sequence': seq,
                'data': data,
                'state': 'pre-prepare',
                'prepares': set(),
                'commits': set()
            }
        
        # Рассылаем prepare сообщение
        prepare_msg = ('prepare', request_id, view, seq, self.node_id)
        self.log[request_id]['prepares'].add(self.node_id)
        self.broadcast(prepare_msg)

    def handle_prepare(self, msg):
        """Обрабатывает prepare сообщение от реплики"""
        _, request_id, view, seq, sender_id = msg
        
        # Проверяем сообщение
        if (request_id not in self.log or 
            view != self.view or 
            seq != self.log[request_id]['sequence']):
            return
            
        # Сохраняем prepare сообщение
        self.log[request_id]['prepares'].add(sender_id)
        
        # Проверяем наличие 2f+1 prepare сообщений (включая свое)
        if (len(self.log[request_id]['prepares']) >= 2 * self.faulty_nodes() + 1 and 
            self.log[request_id]['state'] == 'pre-prepare'):
            
            self.log[request_id]['state'] = 'prepare'
            # Рассылаем commit сообщение
            commit_msg = ('commit', request_id, view, seq, self.node_id)
            self.log[request_id]['commits'].add(self.node_id)
            self.broadcast(commit_msg)

    def handle_commit(self, msg):
        """Обрабатывает commit сообщение от реплики"""
        _, request_id, view, seq, sender_id = msg
        
        # Проверяем сообщение
        if (request_id not in self.log or 
            view != self.view or 
            seq != self.log[request_id]['sequence']):
            return
            
        # Сохраняем commit сообщение
        self.log[request_id]['commits'].add(sender_id)
        
        # Проверяем наличие 2f+1 commit сообщений (включая свое)
        if (len(self.log[request_id]['commits']) >= 2 * self.faulty_nodes() + 1 and 
            self.log[request_id]['state'] == 'prepare'):
            
            self.log[request_id]['state'] = 'commit'
            self.execute(request_id)

    def execute(self, request_id):
        """Выполняет запрос после достижения консенсуса"""
        data = self.log[request_id]['data']
        print(f"Узел {self.node_id} выполняет запрос {request_id}: {data}")
        # Здесь обычно применяется изменение состояния
        
    def faulty_nodes(self):
        """Вычисляет максимальное количество узлов, которое может выдержать система"""
        return (len(self.nodes) - 1) // 3
