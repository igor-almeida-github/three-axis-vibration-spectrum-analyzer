import mysql.connector
import matplotlib
from matplotlib import style as plot_style
import serial
from serial.tools.list_ports import comports
from time import time as agora
from collections import deque
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from statistics import mean
from PIL import ImageTk
from csv import writer
import datetime
import os

matplotlib.use("TkAgg")
plot_style.use("ggplot")


class MonitorSerial(serial.Serial):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__pacotes_perdidos = 0

    def ler_pacote(self, timeout) -> list:
        """
        Tenta ler um pacote no buffer serial.

        Se um pacote válido for lido:
        - Retorna uma lista contendo os três valores de aceleração (eixos x, y, z) em m/s² no formato float e
          o tempo entre a amostra atual e a última em segundos.

        Se um pacote válido não for recebido até o final do tempo 'timeout':
        - Retorna uma lista vazia
        """
        start_ler_pacote = agora()
        pacote = []
        while True:
            leitura = self.read()
            pacote.append(leitura)
            if pacote[-2:] == [b'\r', b'\n']:
                if len(pacote) == 10:
                    pacote = pacote[0:-2]
                    pacote_decodificado = self.__decodificar_pacote(pacote)
                    return pacote_decodificado
                elif len(pacote) > 10:
                    self.__pacotes_perdidos += 1
                    pacote = []
            if agora() - start_ler_pacote > timeout:
                return []

    @staticmethod
    def __decodificar_pacote(pacote):
        """Decodifica um pacote de dados de aceleração e de tempo"""
        pacote_decodificado = []

        # Decodificando Acelerações:
        for indice in (0, 2, 4):
            aceleracao = pacote[indice] + pacote[indice + 1]
            aceleracao_decodificada = int.from_bytes(aceleracao, byteorder='big', signed=True) * 2 * 9.8 / 32767
            pacote_decodificado.append(aceleracao_decodificada)

        # Decodificando tempo:
        delta_tempo = pacote[6] + pacote[7]
        delta_tempo_decodificado = int.from_bytes(delta_tempo, byteorder='big', signed=False) * 0.25 * (10 ** -6)
        pacote_decodificado.append(delta_tempo_decodificado)

        return pacote_decodificado

    @staticmethod
    def portas_disponiveis() -> list:
        """Retorna uma lista com o nome das portas seriais disponíveis"""
        portas_seriais_disponiveis = [porta.device for porta in comports()]
        return portas_seriais_disponiveis


class InterfaceGrafica(tk.Tk):
    __numero_de_pontos_no_grafico = 1024
    __numero_de_pontos_na_fft = 1024

    def __init__(self, monitor_serial, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configurações da janela
        self.title("Sistema de monitoramento de Vibração")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        width, height = self.winfo_screenwidth(), self.winfo_screenheight()
        self.state('normal')
        self.geometry(f"{width}x{height}")
        self.minsize(width, height)
        self.maxsize(width, height)
        self.state('zoomed')

        # Estilos
        self.__style = ttk.Style(self)
        self.__style.theme_use('clam')
        self.__style.configure('Frames.TFrame',
                               background='#DEDEDE'
                               )
        self.__style.configure('FramesClaros.TFrame',
                               background='#F0F0F0'
                               )
        self.__style.configure('LabelCorDeFundo.TLabel',
                               background='#DEDEDE'
                               )
        self.__style.configure('RadioCorDeFundo.TRadiobutton',
                               background='#DEDEDE',
                               foreground='#353535',
                               font=('Segoe UI', 11)
                               )
        self.__style.configure('LabelStatusText.TLabel',
                               background='#DEDEDE',
                               foreground='#595959',
                               font=('Segoe UI', 20)
                               )
        self.__style.configure('LabelStatusVar.TLabel',
                               background='#DEDEDE',
                               foreground='#E00000',
                               font=('Segoe UI', 15)
                               )
        self.__style.configure('LabelModo.TLabel',
                               background='#DEDEDE',
                               foreground='#595959',
                               font=('Segoe UI', 20)
                               )
        self.__style.configure('LabelGravacoes.TLabel',
                               background='#DEDEDE',
                               foreground='#454545',
                               font=('Segoe UI', 15)
                               )
        self.__style.configure('LabelLog.TLabel',
                               background='#DEDEDE',
                               foreground='#353535',
                               font=('Segoe UI', 11)
                               )
        self.__style.configure('LabelJanelaParar.TLabel',
                               background='#F0F0F0',
                               font=('Segoe UI', 13)
                               )
        self.__style.configure('BotaoCorDeFundo.TButton',
                               background='#DEDEDE',
                               borderwidth=0
                               )
        self.__style.configure('BotaoBrain.TButton',
                               background='#DEDEDE',
                               borderwidth=1
                               )

        # Variáveis gerais
        self.__ser = monitor_serial
        self.__novos_pacotes_desde_ultima_fft = 128 - self.__numero_de_pontos_na_fft
        self.__numero_ffts_gravadas = 0

        # Frames principais - colocados sobre root
        self.__frame_superior = ttk.Frame(master=self, style='FramesClaros.TFrame')
        self.__frame_superior.rowconfigure(0, weight=1)
        self.__frame_superior.columnconfigure((1, 2, 3), weight=1)
        self.__frame_superior.grid(row=0, column=0, pady=(0, 5), sticky="NSEW")

        self.__frame_inferior = ttk.Frame(master=self, style='FramesClaros.TFrame')
        self.__frame_inferior.rowconfigure(0, weight=1)
        self.__frame_inferior.columnconfigure(1, weight=1)
        self.__frame_inferior.grid(row=2, column=0, pady=(5, 0), sticky="NSEW")

        self.__frame_direita = ttk.Frame(master=self, style='FramesClaros.TFrame')
        self.__frame_direita.rowconfigure(1, weight=1)
        self.__frame_direita.columnconfigure(0, weight=1)
        self.__frame_direita.grid(row=1, column=1, sticky="NSEW", rowspan=3)

        # Widgets e elementos do frame inferior
        self.__frame_record = ttk.Frame(self.__frame_inferior, style='Frames.TFrame')
        self.__frame_record.rowconfigure(0, weight=1)
        self.__frame_record.columnconfigure((0, 1), weight=1)
        self.__frame_record.grid(row=0, column=0, padx=(0, 5), sticky="NSEW")
        self.__play_img = ImageTk.PhotoImage(file=r"assets/play.png")
        self.__pause_img = ImageTk.PhotoImage(file=r"assets/pause.png")
        self.__botao_play_pause = ttk.Button(master=self.__frame_record,
                                             image=self.__play_img,
                                             style='BotaoCorDeFundo.TButton',
                                             command=self.__click_play_pause)
        self.__botao_play_pause.grid(row=0, column=0, padx=(14, 0))
        self.__stop_img = ImageTk.PhotoImage(file=r"assets/stop.png")
        self.__botao_parar = ttk.Button(master=self.__frame_record,
                                        image=self.__stop_img,
                                        style='BotaoCorDeFundo.TButton',
                                        command=self.__click_parar)
        self.__botao_parar.grid(row=0, column=1, padx=(0, 14))
        self.__botao_parar['state'] = 'disabled'

        self.__frame_log = ttk.Frame(self.__frame_inferior, style='Frames.TFrame')
        self.__frame_log.rowconfigure(1, weight=1)
        self.__frame_log.columnconfigure(0, weight=1)
        self.__frame_log.grid(row=0, column=1, sticky="NSEW")
        ttk.Label(master=self.__frame_log, text=' Log', style='LabelLog.TLabel')\
            .grid(row=0, column=0, padx=(18, 0), sticky='W')
        self.__log = tk.Text(self.__frame_log, height=6)
        self.__log.grid(row=1, column=0, sticky="NSEW", padx=(18, 5))
        self.__log_scroll = ttk.Scrollbar(self.__frame_log, orient='vertical', command=self.__log.yview)
        self.__log_scroll.grid(row=1, column=1, padx=(0, 5), sticky='NS')
        self.__log['yscrollcommand'] = self.__log_scroll.set
        self.__log['state'] = 'disabled'
        self.__botao_limpar_log = ttk.Button(master=self.__frame_log,
                                             text='Limpar',
                                             command=self.__click_limpar)
        self.__botao_limpar_log.grid(row=2, column=0, padx=(18, 0), pady=(2, 6), sticky="W")

        # Elementos da lateral direita
        self.__frame_botoes_direita = ttk.Frame(master=self, style='Frames.TFrame')
        self.__frame_botoes_direita.rowconfigure((0, 1, 2), weight=1)
        self.__frame_botoes_direita.columnconfigure(0, weight=1)
        self.__frame_botoes_direita.grid(row=2, column=1, padx=(9, 0), sticky="NSEW")
        self.__botao_excluir = ttk.Button(master=self.__frame_botoes_direita,
                                          text="Excluir", command=self.__click_excluir)
        self.__botao_excluir.grid(row=0, column=0, ipadx=25, ipady=2)
        self.__botao_editar = ttk.Button(master=self.__frame_botoes_direita, text="Editar", command=self.__click_editar)
        self.__botao_editar.grid(row=1, column=0, ipadx=25, ipady=2)
        self.__botao_ver_detalhes = ttk.Button(master=self.__frame_botoes_direita, text="Ver detalhes", command=None)
        self.__botao_ver_detalhes.grid(row=2, column=0, ipadx=25, ipady=2)
        self.__botao_excluir['state'] = 'disabled'
        self.__botao_editar['state'] = 'disabled'
        self.__botao_ver_detalhes['state'] = 'disabled'

        ttk.Label(master=self, text='  Gravações Registradas', style='LabelGravacoes.TLabel')\
            .grid(row=0, column=1,  padx=(9, 0), sticky='NSEW')

        self.__frame_selecao_gravacoes = ttk.Frame(master=self, style='Frames.TFrame')
        self.__frame_selecao_gravacoes.rowconfigure(1, weight=1)
        self.__frame_selecao_gravacoes.columnconfigure(0, weight=1)
        self.__frame_selecao_gravacoes.grid(row=1, column=1, padx=(9, 0), sticky="NSEW")
        self.__gravacoes = tk.StringVar(value=())
        self.__listbox_gravacoes = tk.Listbox(self.__frame_selecao_gravacoes,
                                              listvariable=self.__gravacoes,
                                              width=35,
                                              selectmode='extended'
                                              )
        self.__listbox_gravacoes.grid(row=1, column=0, padx=(7, 0), sticky="NSEW")
        self.__update_listbox()
        self.__listbox_gravacoes.bind('<<ListboxSelect>>', self.__list_box_change_selection)
        self.__listbox_gravacoes_scroll = ttk.Scrollbar(self.__frame_selecao_gravacoes,
                                                        orient='vertical',
                                                        command=self.__listbox_gravacoes.yview)
        self.__listbox_gravacoes_scroll.grid(row=0, column=1, sticky='NS', rowspan=2)
        self.__listbox_gravacoes['yscrollcommand'] = self.__listbox_gravacoes_scroll.set
        self.__input_gravacoes_var = tk.StringVar()
        self.__input_gravacoes = ttk.Entry(
            master=self.__frame_selecao_gravacoes,
            textvariable=self.__input_gravacoes_var
        )
        self.__input_gravacoes.grid(row=0, column=0, padx=(7, 0), sticky="NSEW")

        # Elementos do frame superior
        self.__logo_ufv_frame = ttk.Frame(self.__frame_superior, style='Frames.TFrame')
        self.__logo_ufv_frame.rowconfigure(0, weight=1)
        self.__logo_ufv_frame.columnconfigure(0, weight=1)
        self.__logo_ufv_frame.grid(row=0, column=0, padx=(0, 5), sticky="NSEW")
        self.__ufv_img = ImageTk.PhotoImage(file=r"assets/ufv.png")
        self.__ufv_img_label = ttk.Label(master=self.__logo_ufv_frame,
                                         image=self.__ufv_img,
                                         style='LabelCorDeFundo.TLabel')
        self.__ufv_img_label.image = self.__ufv_img
        self.__ufv_img_label.grid(row=0, column=0, padx=(50, 60))

        self.__status_frame = ttk.Frame(self.__frame_superior, style='Frames.TFrame')
        self.__status_frame.rowconfigure(0, weight=1)
        self.__status_frame.columnconfigure(3, weight=1)
        self.__status_frame.grid(row=0, column=1, padx=(0, 5), sticky="NSEW")
        ttk.Label(master=self.__status_frame, text='STATUS: ', style='LabelStatusText.TLabel')\
            .grid(row=0, column=0, padx=(9, 0), sticky='W')
        self.__status_var = tk.StringVar(value='Gravação parada')
        ttk.Label(master=self.__status_frame, textvariable=self.__status_var, style='LabelStatusVar.TLabel', width=20)\
            .grid(row=0, column=1,  sticky='W')
        self.__modo_frame = ttk.Frame(self.__frame_superior, style='Frames.TFrame')
        self.__modo_frame.rowconfigure((0, 1), weight=1)
        self.__modo_frame.columnconfigure((0, 1), weight=1)
        self.__modo_frame.grid(row=0, column=2, sticky="NSEW")
        ttk.Label(master=self.__modo_frame, text='MODO: ', style='LabelModo.TLabel').\
            grid(row=0, column=0, padx=(50, 0), rowspan=2)
        self.__modo = tk.StringVar(value='Gravação')
        opcao1 = ttk.Radiobutton(
            master=self.__modo_frame,
            text='Gravação',
            variable=self.__modo,
            value='Gravação',
            command=None,
            style='RadioCorDeFundo.TRadiobutton'
        )
        opcao2 = ttk.Radiobutton(
            master=self.__modo_frame,
            text='Visualização',
            variable=self.__modo,
            value='Visualização',
            command=None,
            style='RadioCorDeFundo.TRadiobutton'
        )
        opcao1.grid(row=0, column=1, padx=(0, 50), sticky='W')
        opcao2.grid(row=1, column=1, padx=(0, 50), sticky='W')

        self.__botao_treinamento_frame = ttk.Frame(self.__frame_superior, style='Frames.TFrame')
        self.__botao_treinamento_frame.rowconfigure(0, weight=1)
        self.__botao_treinamento_frame.columnconfigure(0, weight=1)
        self.__treinamento_img = ImageTk.PhotoImage(file=r"assets/brain.png")
        self.__botao_treinamento_frame.grid(row=0, column=3, padx=(5, 0), sticky="NSEW")
        self.__botao_treinamento = ttk.Button(master=self.__botao_treinamento_frame,
                                              image=self.__treinamento_img,
                                              style='BotaoBrain.TButton',
                                              command=None)
        self.__botao_treinamento.grid(row=0, column=0, padx=(80, 80), pady=(5, 5))

        # Criação da figura do gráfico
        figura = Figure(figsize=(5, 5), dpi=110)
        figura.subplots_adjust(hspace=0.6)
        self.__subplot_accx = figura.add_subplot(321)
        self.__subplot_accy = figura.add_subplot(323)
        self.__subplot_accz = figura.add_subplot(325)

        self.__subplot_accx_fft = figura.add_subplot(322)
        self.__subplot_accy_fft = figura.add_subplot(324)
        self.__subplot_accz_fft = figura.add_subplot(326)

        self.__canvas = FigureCanvasTkAgg(figura, self)
        self.__canvas.draw()
        self.__canvas.get_tk_widget().grid(row=1, column=0, sticky="NSEW")

        # Inicializa variáveis
        # Tempo
        self.__pontos_accx = deque(
            [0 for i in range(self.__numero_de_pontos_no_grafico)],
            maxlen=self.__numero_de_pontos_no_grafico
        )
        self.__pontos_accy = deque(
            [0 for i in range(self.__numero_de_pontos_no_grafico)],
            maxlen=self.__numero_de_pontos_no_grafico
        )
        self.__pontos_accz = deque(
            [0 for i in range(self.__numero_de_pontos_no_grafico)],
            maxlen=self.__numero_de_pontos_no_grafico
        )
        self.__pontos_delta_tempo = deque(
            [0 for i in range(self.__numero_de_pontos_na_fft)],
            maxlen=self.__numero_de_pontos_na_fft
        )

        # Frequência
        self.__fft_freq = []

        # Inicia a recepção serial
        self.__coleta_pacotes_task = self.after(0, self.__coleta_pacote_serial)

    def __coleta_pacote_serial(self):
        """Atualiza os atributos com novos pontos de aceleração coletados na porta serial e atualiza ffts"""

        # Atualiza os pontos no dominio do tempo
        while self.__ser.inWaiting() > 20:
            accx, accy, accz, delta_tempo = self.__ser.ler_pacote(timeout=2)
            self.__pontos_accx.append(accx)
            self.__pontos_accy.append(accy)
            self.__pontos_accz.append(accz)
            self.__pontos_delta_tempo.append(delta_tempo)
            self.__novos_pacotes_desde_ultima_fft += 1

        # Atualiza os pontos da fft a cada 512 novos pacotes recebidos (pelo menos)
        if self.__novos_pacotes_desde_ultima_fft >= 256:
            self.__atualiza_fft()
            if self.__status_var.get()[0:8] == 'Gravando':
                self.__salvar_fft_csv()
        self.__coleta_pacotes_task = self.after(2, self.__coleta_pacote_serial)

    def __atualiza_fft(self):
        fs = 1 / mean(self.__pontos_delta_tempo)
        self.__novos_pacotes_desde_ultima_fft = 0
        self.__fft_accx, self.__fft_freq = self.calcula_fft_abs(
            list(self.__pontos_accx)[-self.__numero_de_pontos_na_fft:],
            freq_amostragem=fs
        )
        self.__fft_accy, _ = self.calcula_fft_abs(
            list(self.__pontos_accy)[-self.__numero_de_pontos_na_fft:],
            freq_amostragem=fs
        )
        self.__fft_accz, _ = self.calcula_fft_abs(
            list(self.__pontos_accz)[-self.__numero_de_pontos_na_fft:],
            freq_amostragem=fs
        )
        self.__update_graficos()

    def __update_graficos(self):
        """Atualiza os gráficos na tela"""
        # Limpa os pontos anteriores dos gráficos
        self.__subplot_accx.clear()
        self.__subplot_accy.clear()
        self.__subplot_accz.clear()
        self.__subplot_accx_fft.clear()
        self.__subplot_accy_fft.clear()
        self.__subplot_accz_fft.clear()

        # Ajusta os eixos dos gráficos
        self.__subplot_accx.set_xlim(0, self.__numero_de_pontos_no_grafico)
        self.__subplot_accy.set_xlim(0, self.__numero_de_pontos_no_grafico)
        self.__subplot_accz.set_xlim(0, self.__numero_de_pontos_no_grafico)
        self.__subplot_accx_fft.set_xlim(0, self.__fft_freq[-1])
        self.__subplot_accy_fft.set_xlim(0, self.__fft_freq[-1])
        self.__subplot_accz_fft.set_xlim(0, self.__fft_freq[-1])

        # Atualiza os títulos dos gráficos
        self.__subplot_accx.set_title("accX - Vertical:m/s²  Horizontal:ms", fontsize=9, color='k')
        self.__subplot_accy.set_title("accY - Vertical:m/s²  Horizontal:ms", fontsize=9, color='r')
        self.__subplot_accz.set_title("accZ - Vertical:m/s²  Horizontal:ms", fontsize=9, color='olive')

        self.__subplot_accx_fft.set_title("FFT_accX - Vertical:m/s²  Horizontal:hz", fontsize=9, color='k')
        self.__subplot_accy_fft.set_title("FFT_accY - Vertical:m/s²  Horizontal:hz", fontsize=9, color='r')
        self.__subplot_accz_fft.set_title("FFT_accZ - Vertical:m/s²  Horizontal:hz", fontsize=9, color='olive')

        # Insere os novos pontos
        self.__subplot_accx.plot(self.__pontos_accx, linewidth=0.7, linestyle='dotted', color='k')
        self.__subplot_accy.plot(self.__pontos_accy, linewidth=0.7, linestyle='dotted', color='r')
        self.__subplot_accz.plot(self.__pontos_accz, linewidth=0.7, linestyle='dotted', color='olive')
        self.__subplot_accx_fft.plot(self.__fft_freq, self.__fft_accx, linewidth=0.7, linestyle='dotted', color='k')
        self.__subplot_accy_fft.plot(self.__fft_freq, self.__fft_accy, linewidth=0.7, linestyle='dotted', color='r')
        self.__subplot_accz_fft.plot(self.__fft_freq, self.__fft_accz, linewidth=0.7, linestyle='dotted', color='olive')
        self.__canvas.draw()

    def __salvar_fft_csv(self):
        """
        Salva ffts x, y e z em arquivo csv
        """
        diretorio = 'C:/Users/igor_/Desktop/csv_dump/'
        with open(diretorio + 'temp_name.csv', 'a', encoding='UTF-8', newline='') as arquivo:
            escritor_csv = writer(arquivo)
            linha = list(self.__fft_accx) + list(self.__fft_accy) + list(self.__fft_accz)
            escritor_csv.writerow(linha)
        self.__numero_ffts_gravadas += 1
        self.__status_var.set(f'Gravando ({self.__numero_ffts_gravadas})')

    def __update_listbox(self):
        conn = InterfaceGrafica.__conectar_mysql('fft_dados')
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM registros_de_vibracao ORDER BY id ASC;")
        self.__nomes_registros_vibracao = tuple(tupla[0] for tupla in cursor.fetchall())
        InterfaceGrafica.__desconectar_mysql(conn)
        self.__gravacoes.set(self.__nomes_registros_vibracao)

    def __click_excluir(self):
        resposta = messagebox.askquestion(title='Excluir selecionados?',
                                          message='Tem certeza que deseja excluir os itens selecionados?')
        if resposta == 'no':
            return
        data_hora = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
        indices_selecionados = self.__listbox_gravacoes.curselection()
        nomes_selecionados = tuple(self.__listbox_gravacoes.get(idx) for idx in indices_selecionados)
        conn = InterfaceGrafica.__conectar_mysql('fft_dados')
        cursor = conn.cursor()
        self.__log['state'] = 'normal'
        for nome in nomes_selecionados:
            if os.path.exists(f'C:/Users/igor_/Desktop/csv_dump/{nome}.csv'):
                os.remove(f'C:/Users/igor_/Desktop/csv_dump/{nome}.csv')
            cursor.execute(f"SELECT id FROM registros_de_vibracao WHERE nome = '{nome}';")
            id_para_excluir = cursor.fetchall()[0][0]
            cursor.execute(f"DELETE FROM descricoes WHERE id_registro_de_vibracao = '{id_para_excluir}';")
            cursor.execute(f"DELETE FROM registros_de_vibracao WHERE id = '{id_para_excluir}';")
            self.__log.insert('end', f'({data_hora}): Gravação "{nome}" foi excluída. \n')
        self.__log['state'] = 'disabled'
        self.__log.see('end')
        conn.commit()
        InterfaceGrafica.__desconectar_mysql(conn)
        self.__update_listbox()
        self.__botao_excluir['state'] = 'disabled'
        self.__botao_editar['state'] = 'disabled'
        self.__botao_ver_detalhes['state'] = 'disabled'

    def __list_box_change_selection(self, event):
        indices_selecionados = self.__listbox_gravacoes.curselection()
        if len(indices_selecionados) == 0:
            self.__botao_excluir['state'] = 'disabled'
            self.__botao_editar['state'] = 'disabled'
            self.__botao_ver_detalhes['state'] = 'disabled'
        elif len(indices_selecionados) == 1:
            self.__botao_excluir['state'] = 'normal'
            self.__botao_editar['state'] = 'normal'
            self.__botao_ver_detalhes['state'] = 'normal'
        elif len(indices_selecionados) > 1:
            self.__botao_excluir['state'] = 'normal'
            self.__botao_editar['state'] = 'disabled'
            self.__botao_ver_detalhes['state'] = 'disabled'

    def __click_play_pause(self):
        data_hora = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
        if self.__status_var.get() == 'Gravação parada':
            self.__log['state'] = 'normal'
            self.__log.insert('end', f'({data_hora}): STATUS alterado para "Gravando". \n')
            self.__log['state'] = 'disabled'
            self.__botao_play_pause['image'] = self.__pause_img
            self.__status_var.set('Gravando (0)')
            self.__style.configure('LabelStatusVar.TLabel',
                                   background='#DEDEDE',
                                   foreground='#409540',
                                   font=('Segoe UI', 15)
                                   )
            self.__botao_parar['state'] = 'normal'
            if os.path.exists('C:/Users/igor_/Desktop/csv_dump/temp_name.csv'):
                os.remove('C:/Users/igor_/Desktop/csv_dump/temp_name.csv')
        elif self.__status_var.get()[0:8] == 'Gravando':
            self.__log['state'] = 'normal'
            self.__log.insert('end', f'({data_hora}): STATUS alterado para "Gravação pausada". \n')
            self.__log['state'] = 'disabled'
            self.__botao_play_pause['image'] = self.__play_img
            self.__status_var.set(f'Gravação pausada ({self.__numero_ffts_gravadas})')
            self.__style.configure('LabelStatusVar.TLabel',
                                   background='#DEDEDE',
                                   foreground='#B09000',
                                   font=('Segoe UI', 15)
                                   )
        elif self.__status_var.get()[0:16] == 'Gravação pausada':
            self.__log['state'] = 'normal'
            self.__log.insert('end', f'({data_hora}): STATUS alterado para "Gravando". \n')
            self.__log['state'] = 'disabled'
            self.__botao_play_pause['image'] = self.__pause_img
            self.__status_var.set(f'Gravando ({self.__numero_ffts_gravadas})')
            self.__style.configure('LabelStatusVar.TLabel',
                                   background='#DEDEDE',
                                   foreground='#409540',
                                   font=('Segoe UI', 15)
                                   )
        self.__log.see('end')

    def __click_editar(self):

        indice_selecionado = self.__listbox_gravacoes.curselection()[0]
        nome_selecionado = self.__listbox_gravacoes.get(indice_selecionado)

        descricao = InterfaceGrafica.__ver_descricao_fft_dados_mysql(nome_selecionado)

        self.__toplevel = tk.Toplevel()
        self.__toplevel.grab_set()
        x = self.winfo_x()
        y = self.winfo_y()
        self.__toplevel.geometry("+%d+%d" % (x + 500, y + 250))
        self.__toplevel.title("Editar gravação")
        self.__toplevel.rowconfigure(3, weight=1)
        self.__toplevel.columnconfigure((0, 1), weight=1)
        self.__toplevel.resizable('False', 'False')

        # Botões
        botao_salvar_alteracoes = ttk.Button(master=self.__toplevel, text="Salvar alterações",
                                             command=self.__click_editar_salvar_alteracoes)
        botao_salvar_alteracoes.grid(row=4, column=0, pady=(0, 5), ipadx=20, ipady=1)
        botao_cancelar = ttk.Button(master=self.__toplevel, text="Cancelar", command=self.__toplevel.destroy)
        botao_cancelar.grid(row=4, column=1, pady=(0, 5), ipadx=20, ipady=1)

        # Descrição
        ttk.Label(master=self.__toplevel, text="Descrição (Opcional)", style='LabelJanelaParar.TLabel') \
            .grid(row=2, column=0, padx=(10, 10), sticky='NSEW', columnspan=2)
        self.__descricao_text = tk.Text(self.__toplevel, height=4, width=50)
        self.__descricao_text.grid(row=3, column=0, padx=(10, 10), pady=(0, 10), columnspan=2)
        self.__descricao_text.insert('end', descricao)

        # Nome
        ttk.Label(master=self.__toplevel, text="Nome (Obrigatório)", style='LabelJanelaParar.TLabel') \
            .grid(row=0, column=0, padx=(10, 10), sticky='NSEW', columnspan=2)
        self.__input_nome_var = tk.StringVar(value=nome_selecionado)
        self.__input_nome = ttk.Entry(
            master=self.__toplevel,
            textvariable=self.__input_nome_var,
            width=50
        )
        self.__input_nome.grid(row=1, column=0, padx=(10, 10), pady=(0, 10), sticky="W", columnspan=2)

    def __click_editar_salvar_alteracoes(self):
        indice_selecionado = self.__listbox_gravacoes.curselection()[0]
        nome_selecionado = self.__listbox_gravacoes.get(indice_selecionado)
        novo_nome = self.__input_nome_var.get().lstrip().rstrip()

        if novo_nome == '':
            messagebox.showinfo('Nome não informado', 'O nome deve ser informado antes de salvar!')
            return
        if novo_nome in self.__nomes_registros_vibracao and novo_nome != nome_selecionado:
            messagebox.showinfo('Nome repetido', 'Já existe um registro com esse nome. Favor escolha outro nome!')
            return

        nova_descricao = self.__descricao_text.get('1.0', 'end').lstrip().rstrip()
        InterfaceGrafica.__alterar_fft_dados_mysql(nome_selecionado, novo_nome, nova_descricao)

        data_hora = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
        self.__log['state'] = 'normal'
        self.__log.insert('end', f'({data_hora}): Alterações em "{novo_nome}" salvas com sucesso. \n')
        self.__log['state'] = 'disabled'
        self.__log.see('end')

        self.__update_listbox()

        if os.path.exists(f'C:/Users/igor_/Desktop/csv_dump/{nome_selecionado}.csv'):
            os.rename(f'C:/Users/igor_/Desktop/csv_dump/{nome_selecionado}.csv',
                      f'C:/Users/igor_/Desktop/csv_dump/{novo_nome}.csv')

        self.__toplevel.destroy()

    def __click_parar(self):
        self.__toplevel = tk.Toplevel()
        self.__toplevel.grab_set()
        x = self.winfo_x()
        y = self.winfo_y()
        self.__toplevel.geometry("+%d+%d" % (x + 500, y + 250))
        self.__toplevel.title("Salvar gravação")
        self.__toplevel.rowconfigure(3, weight=1)
        self.__toplevel.columnconfigure((0, 1, 2), weight=1)
        self.__toplevel.resizable('False', 'False')
        self.after_cancel(self.__coleta_pacotes_task)

        data_hora = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
        if self.__status_var.get()[0:8] == 'Gravando':
            self.__log['state'] = 'normal'
            self.__log.insert('end', f'({data_hora}): STATUS alterado para "Gravação pausada". \n')
            self.__log['state'] = 'disabled'
            self.__botao_play_pause['image'] = self.__play_img
            self.__status_var.set(f'Gravação pausada ({self.__numero_ffts_gravadas})')
            self.__style.configure('LabelStatusVar.TLabel',
                                   background='#DEDEDE',
                                   foreground='#B09000',
                                   font=('Segoe UI', 15)
                                   )
            self.__log.see('end')

        # Botões
        botao_salvar = ttk.Button(master=self.__toplevel, text="Salvar", command=self.__click_parar_salvar)
        botao_salvar.grid(row=4, column=0, pady=(0, 5), ipadx=20, ipady=1)
        botao_descartar = ttk.Button(master=self.__toplevel, text="Descartar", command=self.__click_parar_descartar)
        botao_descartar.grid(row=4, column=1, pady=(0, 5), ipadx=20, ipady=1)
        botao_cancelar = ttk.Button(master=self.__toplevel, text="Cancelar", command=self.__click_parar_cancelar)
        botao_cancelar.grid(row=4, column=2, pady=(0, 5), ipadx=20, ipady=1)

        # Descrição
        ttk.Label(master=self.__toplevel, text="Descrição (Opcional)", style='LabelJanelaParar.TLabel') \
            .grid(row=2, column=0, padx=(10, 10), sticky='NSEW', columnspan=3)
        self.__descricao_text = tk.Text(self.__toplevel, height=4, width=50)
        self.__descricao_text.grid(row=3, column=0, padx=(10, 10), pady=(0, 10), columnspan=3)

        # Nome
        ttk.Label(master=self.__toplevel, text="Nome (Obrigatório)", style='LabelJanelaParar.TLabel') \
            .grid(row=0, column=0, padx=(10, 10), sticky='NSEW', columnspan=3)
        self.__input_nome_var = tk.StringVar()
        self.__input_nome = ttk.Entry(
            master=self.__toplevel,
            textvariable=self.__input_nome_var,
            width=50
        )
        self.__input_nome.grid(row=1, column=0, padx=(10, 10), pady=(0, 10), sticky="W", columnspan=3)

    def __click_parar_salvar(self):
        nome = self.__input_nome_var.get().lstrip().rstrip()
        if nome == '':
            messagebox.showinfo('Nome não informado', 'O nome deve ser informado antes de salvar!')
            return
        if nome in self.__nomes_registros_vibracao:
            messagebox.showinfo('Nome repetido', 'Já existe um registro com esse nome. Favor escolha outro nome!')
            return
        descricao = self.__descricao_text.get('1.0', 'end').lstrip().rstrip()
        self.__escrever_fft_dados_mysql(nome, self.__numero_ffts_gravadas, descricao)
        data_hora = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
        self.__log['state'] = 'normal'
        self.__log.insert('end', f'({data_hora}): Gravação salva no banco de dados. \n')
        self.__log.insert('end', f'({data_hora}): STATUS alterado para "Gravação parada". \n')
        self.__log['state'] = 'disabled'
        self.__botao_play_pause['image'] = self.__play_img
        self.__status_var.set('Gravação parada')
        self.__style.configure('LabelStatusVar.TLabel',
                               background='#DEDEDE',
                               foreground='#E00000',
                               font=('Segoe UI', 15)
                               )
        self.__log.see('end')
        self.__botao_parar['state'] = 'disabled'
        self.__numero_ffts_gravadas = 0
        os.rename('C:/Users/igor_/Desktop/csv_dump/temp_name.csv', f'C:/Users/igor_/Desktop/csv_dump/{nome}.csv')
        self.__update_listbox()
        self.__toplevel.destroy()
        self.__coleta_pacotes_task = self.after(0, self.__coleta_pacote_serial)

    def __click_parar_descartar(self):
        data_hora = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
        self.__log['state'] = 'normal'
        self.__log.insert('end', f'({data_hora}): Gravação descartada. \n')
        self.__log.insert('end', f'({data_hora}): STATUS alterado para "Gravação parada". \n')
        self.__log['state'] = 'disabled'
        self.__botao_play_pause['image'] = self.__play_img
        self.__status_var.set('Gravação parada')
        self.__style.configure('LabelStatusVar.TLabel',
                               background='#DEDEDE',
                               foreground='#E00000',
                               font=('Segoe UI', 15)
                               )
        self.__log.see('end')
        os.remove('C:/Users/igor_/Desktop/csv_dump/temp_name.csv')
        self.__botao_parar['state'] = 'disabled'
        self.__numero_ffts_gravadas = 0
        self.__toplevel.destroy()
        self.__coleta_pacotes_task = self.after(0, self.__coleta_pacote_serial)

    def __click_parar_cancelar(self):
        self.__toplevel.destroy()
        self.__coleta_pacotes_task = self.after(0, self.__coleta_pacote_serial)

    def __click_limpar(self):
        self.__log['state'] = 'normal'
        self.__log.delete('1.0', tk.END)
        self.__log['state'] = 'disabled'

    @staticmethod
    def __conectar_mysql(db):
        """
        Função para conectar ao servidor mysql
        """
        try:
            conn = mysql.connector.connect(
                host='127.0.0.1',
                port=3306,
                user='igor',
                password='123456',
                database=f'{db}'
            )
            return conn
        except mysql.connector.Error as err:
            print(f'Erro na conexão ao MySQL Server: {err}')

    @staticmethod
    def __escrever_fft_dados_mysql(nome: str, quantidade_de_ffts_coletadas: int, descricao: str = ''):
        conn = InterfaceGrafica.__conectar_mysql('fft_dados')
        cursor = conn.cursor()
        diretorio_fft_csv = f'C:/Users/igor_/Desktop/csv_dump/{nome}.csv'
        cursor.execute(f"INSERT INTO registros_de_vibracao "
                       f"VALUES ("
                       f"NULL, "
                       f"'{nome}', "
                       f"CURDATE(), "
                       f"CURTIME(), "
                       f"'{diretorio_fft_csv}', "
                       f"{quantidade_de_ffts_coletadas});")
        cursor.execute("SELECT LAST_INSERT_ID()")
        id_registro_de_vibracao = cursor.fetchall()[0][0]
        if descricao:
            cursor.execute(f"INSERT INTO descricoes VALUES (NULL, {id_registro_de_vibracao}, '{descricao}')")
        conn.commit()
        InterfaceGrafica.__desconectar_mysql(conn)

    @staticmethod
    def __alterar_fft_dados_mysql(nome: str, novo_nome: str, nova_descricao: str):
        conn = InterfaceGrafica.__conectar_mysql('fft_dados')
        cursor = conn.cursor()

        # registros_de_vibracao
        diretorio_fft_csv = f'C:/Users/igor_/Desktop/csv_dump/{novo_nome}.csv'
        cursor.execute(f"SELECT id FROM registros_de_vibracao WHERE nome = '{nome}';")
        id_para_alterar = cursor.fetchall()[0][0]
        cursor.execute(f"UPDATE registros_de_vibracao SET nome = '{novo_nome}', "
                       f"diretorio_fft_csv = '{diretorio_fft_csv}' WHERE id = {id_para_alterar}")

        # descricoes
        descricao = InterfaceGrafica.__ver_descricao_fft_dados_mysql(nome)
        if descricao and not nova_descricao:
            """Se havia uma descrição e deseja-se remove-la"""
            cursor.execute(f"DELETE FROM descricoes WHERE id_registro_de_vibracao = '{id_para_alterar}';")
        elif not descricao and nova_descricao:
            """Se não havia uma descrição e deseja-se adiciona-la"""
            cursor.execute(f"INSERT INTO descricoes VALUES (NULL, {id_para_alterar}, '{nova_descricao}')")
        elif descricao and nova_descricao:
            """Se não havia uma descrição e deseja-se altera-la ou mante-la"""
            cursor.execute(f"UPDATE descricoes SET descricao = '{nova_descricao}'"
                           f" WHERE id_registro_de_vibracao = {id_para_alterar}")

        conn.commit()
        InterfaceGrafica.__desconectar_mysql(conn)

    @staticmethod
    def __ver_descricao_fft_dados_mysql(nome: str):
        conn = InterfaceGrafica.__conectar_mysql('fft_dados')
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM registros_de_vibracao WHERE nome = '{nome}';")
        id_registro_de_vibracao = cursor.fetchall()[0][0]
        cursor.execute(f"SELECT descricao FROM descricoes WHERE id_registro_de_vibracao = {id_registro_de_vibracao}")
        busca = cursor.fetchall()
        if busca:
            descricao = busca[0][0]
        else:
            descricao = ''
        return descricao

    @staticmethod
    def __desconectar_mysql(conn):
        """
        Função para desconectar do servidor.
        """
        if conn.is_connected():
            conn.close()

    @staticmethod
    def calcula_fft_abs(sinal, freq_amostragem):
        # Remove offset
        offset = mean(sinal)
        sinal = [ponto - offset for ponto in sinal]
        fft = np.fft.fft(sinal)
        fft_abs = 2 * np.abs(fft) / len(fft)
        fft_abs = fft_abs[0:int(len(fft) / 2)]
        freq = np.linspace(0, freq_amostragem / 2, int(len(fft) / 2))
        return fft_abs, freq


if __name__ == '__main__':
    com = MonitorSerial.portas_disponiveis()[0]
    with MonitorSerial(port=com, baudrate=115200, timeout=1) as ser:
        InterfaceGrafica(monitor_serial=ser).mainloop()




