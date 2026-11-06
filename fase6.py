from datos import *
import threading
import random
import time


class GestorInventario:
    def __init__(self, stock_inicial):
        self.stock_inicial = dict(stock_inicial)
        self.inventario = dict(stock_inicial)
        self.lock = threading.RLock()
        self.condicion = threading.Condition(self.lock)
        self.aceptadas = []
        self.rechazadas = []
        self.repuestas = []
        self.almacen_terminado = False

    def hay_stock(self, producto, cantidad):
        with self.lock:
            return self.inventario[producto] >= cantidad

    def descontar(self, producto, cantidad):
        with self.lock:
            stock_visto = self.inventario[producto]
            self.inventario[producto] = stock_visto - cantidad
            return stock_visto

    def sumar(self, producto, unidades):
        with self.lock:
            self.inventario[producto] += unidades

    def consultar_stock(self, producto):
        with self.lock:
            return self.inventario[producto]

    def vender(self, pedido, num_caja):
        id_pedido, producto, cantidad = pedido

        with self.condicion:
            while not self.hay_stock(producto, cantidad) and not self.almacen_terminado:
                print(f"\nCaja {num_caja} ESPERA reposición de {producto} ({id_pedido})")
                self.condicion.wait()

            if self.hay_stock(producto, cantidad):
                stock_visto = self.descontar(producto, cantidad)
                self.aceptadas.append(pedido)
                return True, stock_visto

            self.rechazadas.append(pedido)
            return False, self.consultar_stock(producto)

    def reponer(self, albaran, producto, unidades):
        with self.condicion:
            self.sumar(producto, unidades)
            self.repuestas.append((albaran, producto, unidades))
            self.condicion.notify_all()

    def cerrar_reposiciones(self):
        with self.condicion:
            self.almacen_terminado = True
            self.condicion.notify_all()

    def revisar_producto(self, producto):
        with self.lock:
            stock_final = self.consultar_stock(producto)

            vendidas = 0
            for pedido in self.aceptadas:
                if pedido[1] == producto:
                    vendidas += pedido[2]

            repuesto = 0
            for reposicion in self.repuestas:
                if reposicion[1] == producto:
                    repuesto += reposicion[2]

            esperado = self.stock_inicial[producto] + repuesto - vendidas
        return stock_final, esperado

gestor = GestorInventario(STOCK_INICIAL)
pedidos = PEDIDOS
num_cajas = NUM_CAJAS
num_revisores = NUM_REVISORES
reposiciones = REPOSICIONES

semaforo = threading.Semaphore(NUM_TERMINALES)
barrera_revision = threading.Barrier(NUM_REVISORES)

lista_cajas = []
lista_revisores = []
resultados_revision = [None] * NUM_REVISORES


def crear_cajas():
    for num in range(num_cajas):
        lista_pedidos = pedidos[num::num_cajas]
        lista_cajas.append(threading.Thread(target=caja_proceso, kwargs={
            "num_caja": num+1,
            "lista_pedidos": lista_pedidos,
        }))


def crear_revisores():
    productos = list(STOCK_INICIAL)
    for num in range(num_revisores):
        lista_revisores.append(threading.Thread(target=revisor_proceso, kwargs={
            "num_revisor": num+1,
            "productos": productos[num::num_revisores],
        }))


def almacen_proceso():
    for albaran, producto, unidades in reposiciones:
        time.sleep(1)
        gestor.reponer(albaran, producto, unidades)
        print(f"Almacén repone {albaran}: +{unidades} x {producto}")

    gestor.cerrar_reposiciones()
    print("\nAlmacén ha terminado todas las reposiciones")


def proceso_pedido(pedido, num_caja):
    id_pedido, producto_pedido, cantidad_pedido = pedido

    with semaforo:
        print(f"\n>>> Caja {num_caja} obtiene una terminal ({id_pedido}) <<<")

        vendido, stock_visto = gestor.vender(pedido, num_caja)

        if vendido:
            print(f"\n> Pedido '{id_pedido}' procesado: {cantidad_pedido} x {producto_pedido} (stock visto: {stock_visto})")
        else:
            print(f"\n> Pedido '{id_pedido}' RECHAZADO: {cantidad_pedido} x {producto_pedido} (no hay stock ni más reposiciones)")

        time.sleep(0.3)
        print(f"\n>>> Caja {num_caja} libera la terminal <<<")


def caja_proceso(num_caja:int, lista_pedidos:list):
    print(f"\n====== Caja Nº{num_caja} ======")
    for pedido in lista_pedidos:
        proceso_pedido(pedido, num_caja)


def revisor_proceso(num_revisor:int, productos:list):
    print(f"\nRevisor {num_revisor} empieza a revisar {len(productos)} productos")
    incoherencias = []

    for producto in productos:
        stock_final, esperado = gestor.revisar_producto(producto)
        if stock_final != esperado or stock_final < 0:
            incoherencias.append(f"INCOHERENCIA en '{producto}': stock final {stock_final}, esperado {esperado}")
        time.sleep(0.3)

    resultados_revision[num_revisor - 1] = incoherencias

    print(f"\nRevisor {num_revisor} ha terminado y ESPERA en la barrera")
    indice = barrera_revision.wait()
    print(f"Revisor {num_revisor} supera la barrera")

    if indice == 0:
        mostrar_resumen()


def mostrar_resumen():
    print("\n====== RESUMEN ======")
    print(f"Aceptados: {len(gestor.aceptadas)} | Rechazados: {len(gestor.rechazadas)}")
    for pedido in gestor.rechazadas:
        print(f"Rechazado '{pedido[0]}': {pedido[2]} x {pedido[1]}")

    incoherente = False
    for incoherencias in resultados_revision:
        for mensaje in incoherencias:
            incoherente = True
            print(mensaje)
    if not incoherente:
        print("Stock coherente: todos los revisores han dado el visto bueno")


def fase6():
    crear_cajas()
    almacen = threading.Thread(target=almacen_proceso)
    for i in lista_cajas:
        i.start()
    almacen.start()
    for i in lista_cajas:
        i.join()
    almacen.join()

    print("\n====== CIERRE DE INVENTARIO ======")
    crear_revisores()
    for i in lista_revisores:
        i.start()
    for i in lista_revisores:
        i.join()


if __name__ == "__main__":
    fase6()