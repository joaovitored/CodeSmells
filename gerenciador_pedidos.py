MAX_PARCELAS_SEM_JUROS = 3
LIMITE_DESCONTO = 500
LIMITE_FRETE_GRATIS = 300

DESCONTO_COMUM = 0.05
DESCONTO_VIP = 0.15
DESCONTO_VIP_MINIMO = 0.10
DESCONTO_FUNCIONARIO = 0.20

FRETE_PE = 12.5
FRETE_NORDESTE = 22.9
FRETE_OUTRAS_REGIOES = 39.9

DESCONTO_PIX = 0.05
TAXA_BOLETO = 2.5
TAXA_PARCELAMENTO = 0.0199

MIN_PARCELAS = 1
MAX_PARCELAS = 12
LIMITE_META_MENSAL = 10000



class DescontoComum:
    def calcular(self, subtotal):
        if subtotal > 500: # LIMITE_DESCONTO
            return subtotal * 0.05 # DESCONTO_COMUM
        return 0

class DescontoVIP:
    def calcular(self, subtotal):
        if subtotal > 500: # LIMITE_DESCONTO
            return subtotal * 0.15 # DESCONTO_VIP
        return subtotal * 0.10 # DESCONTO_VIP_MINIMO

class DescontoFuncionario:
    def calcular(self, subtotal):
        return subtotal * 0.20 # DESCONTO_FUNCIONARIO


class PagamentoPIX:
    def processar(self, total, parcelas):
        # Aplica desconto de 5% do PIX
        return total * 0.95

class PagamentoBoleto:
    def processar(self, total, parcelas):
        # Adiciona taxa de R$ 2.50 do boleto
        return total + 2.5

class PagamentoCartao:
    def processar(self, total, parcelas):
        if parcelas < 1 or parcelas > 12:
            return "ERRO: parcelas invalidas"
        if parcelas > 3: # MAX_PARCELAS_SEM_JUROS
            return total * (1 + 0.0199 * parcelas) # TAXA_PARCELAMENTO
        return total


class Endereco:
    def __init__(self, rua, numero, cidade, uf, cep):
        self.rua = rua
        self.numero = numero
        self.cidade = cidade
        self.uf = uf
        self.cep = cep

    def formatar(self):
        return self.rua + ", " + self.numero + ", " + self.cidade + "/" + self.uf + ", CEP " + self.cep


class PedidoRepository:
    def salvar(self, nome, email, tipo_cliente, pagamento, total, endereco):
        try:
            with open("pedidos.csv", "a", encoding="utf-8") as f:
                f.write(nome + ";" + email + ";" + tipo_cliente + ";" + pagamento + ";"
                        + str(total) + ";" + endereco + "\n")
        except OSError as e:
            print("Falha ao salvar pedido: " + str(e))


class ServicoNotificacao:
    def enviar_confirmacao(self, nome, email, tipo_cliente, total, endereco):
        mensagem = "Ola " + nome + ", seu pedido foi confirmed. "
        if tipo_cliente == "VIP":
            mensagem += "Obrigado por ser VIP! Frete gratis garantido. "
        elif tipo_cliente == "FUNCIONARIO":
            mensagem += "Desconto de colaborador aplicado. "
        mensagem += "Total: R$ " + "%.2f" % total + ". Entrega em: " + endereco
        print("[EMAIL para " + email + "] " + mensagem)


class GerenciadorPedidos:

    def __init__(self):
        self.itens = []
        self.estoque = {}
        self.historico = []
        self.total_vendido = 0
        self.estoque["CANETA"] = 100
        self.estoque["CADERNO"] = 50
        self.estoque["MOCHILA"] = 10
        self.estoque["CALCULADORA"] = 5

        self.estrategias_desconto = {
            "COMUM": DescontoComum(),
            "VIP": DescontoVIP(),
            "FUNCIONARIO": DescontoFuncionario()
        }

        self.estrategias_pagamento = {
            "PIX": PagamentoPIX(),
            "BOLETO": PagamentoBoleto(),
            "CARTAO": PagamentoCartao()
        }

        self.repositorio = PedidoRepository()
        self.notificador = ServicoNotificacao()

    def adicionar_item(self, produto, qtd, preco):
        self.itens.append([produto, str(qtd), str(preco)])

    def _validar_pedido(self, nome, email, cep):
        if nome is None or nome.strip() == "":
            return "ERRO: cliente sem nome"
        if email is None or "@" not in email or "." not in email:
            return "ERRO: email invalido"
        if len(self.itens) == 0:
            return "ERRO: pedido vazio"
        if cep is None or len(cep.replace("-", "")) != 8:
            return "ERRO: cep invalido"
        for item in self.itens:
            if item[0] not in self.estoque:
                return "ERRO: produto inexistente " + item[0]
            if self.estoque[item[0]] < int(item[1]):
                return "ERRO: estoque insuficiente " + item[0]
        return None


    def _calcular_valores(self, tipo_cliente, uf):
        subtotal = 0
        for item in self.itens:
            subtotal += int(item[1]) * float(item[2])

        # desconto = 0
        # if tipo_cliente == "COMUM":
        #     if subtotal > LIMITE_DESCONTO:
        #         desconto = subtotal * DESCONTO_COMUM
        # elif tipo_cliente == "VIP":
        #     if subtotal > LIMITE_DESCONTO:
        #         desconto = subtotal * DESCONTO_VIP
        #     else:
        #         desconto = subtotal * DESCONTO_VIP_MINIMO
        # elif tipo_cliente == "FUNCIONARIO":
        #     desconto = subtotal * DESCONTO_FUNCIONARIO

        # CORRIGIDO:
        estrategia = self.estrategias_desconto.get(tipo_cliente)
        desconto = estrategia.calcular(subtotal) if estrategia else 0

        frete = 0
        if uf == "PE":
            frete = FRETE_PE
        # Nota: Aqui já inclui o "MA", unificando a regra para o Nordeste
        elif (uf == "PB" or uf == "AL" or uf == "RN" or uf == "BA"
                or uf == "SE" or uf == "CE" or uf == "PI" or uf == "MA"):
            frete = FRETE_NORDESTE
        else:
            frete = FRETE_OUTRAS_REGIOES

        if subtotal - desconto > LIMITE_FRETE_GRATIS or tipo_cliente == "VIP":
            frete = 0

        return subtotal, desconto, frete


    def processar_pedido(self, nome, email, tipo_cliente, pagamento, parcelas,
                         rua, numero, cidade, uf, cep):
        erro = self._validar_pedido(nome, email, cep)
        if erro:
            return erro
            
        # subtotal = 0
        # for item in self.itens:
        #     subtotal += int(item[1]) * float(item[2])

        # desconto = 0
        # if tipo_cliente == "COMUM":
        #     if subtotal > LIMITE_DESCONTO:
        #         desconto = subtotal * DESCONTO_COMUM
        # elif tipo_cliente == "VIP":
        #     if subtotal > LIMITE_DESCONTO:
        #         desconto = subtotal * DESCONTO_VIP
        #     else:
        #         desconto = subtotal * DESCONTO_VIP_MINIMO
        # elif tipo_cliente == "FUNCIONARIO":
        #     desconto = subtotal * DESCONTO_FUNCIONARIO
        # else:
        #     return "ERRO: tipo de cliente desconhecido"

        # frete = 0
        # if uf == "PE":
        #     frete = FRETE_PE
        # elif (uf == "PB" or uf == "AL" or uf == "RN" or uf == "BA"
        #       or uf == "SE" or uf == "CE" or uf == "PI" or uf == "MA"):
        #     frete = FRETE_NORDESTE
        # else:
        #     frete = FRETE_OUTRAS_REGIOES

        # if subtotal - desconto > LIMITE_FRETE_GRATIS or tipo_cliente == "VIP":
        #     frete = 0 

        # CORRIGIDO:
        subtotal, desconto, frete = self._calcular_valores(tipo_cliente, uf)
        

        total = subtotal - desconto + frete

        estrategia_pgto = self.estrategias_pagamento.get(pagamento)
        if not estrategia_pgto:
            return "ERRO: forma de pagamento invalida"
            
        resultado_pgto = estrategia_pgto.processar(total, parcelas)
        if isinstance(resultado_pgto, str):
            return resultado_pgto
            
        total = resultado_pgto

        # if pagamento == "PIX":
        #     total = total * (1 - DESCONTO_PIX)
        # elif pagamento == "BOLETO":
        #     total = total + TAXA_BOLETO
        # elif pagamento == "CARTAO":
        #     if parcelas < MIN_PARCELAS or parcelas > MAX_PARCELAS:
        #         return "ERRO: parcelas invalidas"
        #     if parcelas > MAX_PARCELAS_SEM_JUROS:
        #         total = total * (1 + TAXA_PARCELAMENTO * parcelas)
        # else:
        #     return "ERRO: forma de pagamento invalida"

        total = round(total * 100.0) / 100.0


        for item in self.itens:
            self.estoque[item[0]] = self.estoque[item[0]] - int(item[1])

        # endereco = rua + ", " + numero + ", " + cidade + "/" + uf + ", CEP " + cep
        # CORRIGIDO:
        obj_endereco = Endereco(rua, numero, cidade, uf, cep)
        endereco = obj_endereco.formatar()

        self.repositorio.salvar(nome, email, tipo_cliente, pagamento, total, endereco)
        self.notificador.enviar_confirmacao(nome, email, tipo_cliente, total, endereco)

        # try:
        #     f = open("pedidos.csv", "a", encoding="utf-8")
        #     f.write(nome + ";" + email + ";" + tipo_cliente + ";" + pagamento + ";"
        #             + str(total) + ";" + endereco + "\n")
        #     f.close()
        # except OSError as e:
        #     print("Falha ao salvar pedido: " + str(e))

        # mensagem = "Ola " + nome + ", seu pedido foi confirmado. "
        # if tipo_cliente == "VIP":
        #     mensagem += "Obrigado por ser VIP! Frete gratis garantido. "
        # elif tipo_cliente == "FUNCIONARIO":
        #     mensagem += "Desconto de colaborador aplicado. "
        # mensagem += "Total: R$ " + "%.2f" % total + ". Entrega em: " + endereco
        # print("[EMAIL para " + email + "] " + mensagem)

        self.historico.append(nome + "|" + tipo_cliente + "|" + str(total))
        self.total_vendido += total
        self.itens.clear()
        return "OK: " + "%.2f" % total

        
    def calcular_orcamento(self, tipo_cliente, uf):
        # subtotal = 0
        # for item in self.itens:
        #     subtotal += int(item[1]) * float(item[2])

        # desconto = 0
        # if tipo_cliente == "COMUM":
        #     if subtotal > LIMITE_DESCONTO:
        #         desconto = subtotal * DESCONTO_COMUM
        # elif tipo_cliente == "VIP":
        #     if subtotal > LIMITE_DESCONTO:
        #         desconto = subtotal * DESCONTO_VIP
        #     else:
        #         desconto = subtotal * DESCONTO_VIP_MINIMO
        # elif tipo_cliente == "FUNCIONARIO":
        #     desconto = subtotal * DESCONTO_FUNCIONARIO

        # frete = 0
        # if uf == "PE":
        #     frete = FRETE_PE
        # elif (uf == "PB" or uf == "AL" or uf == "RN" or uf == "BA"
        #       or uf == "SE" or uf == "CE" or uf == "PI"):
        #     frete = FRETE_NORDESTE
        # else:
        #     frete = FRETE_OUTRAS_REGIOES

        # if subtotal - desconto > LIMITE_FRETE_GRATIS or tipo_cliente == "VIP":
        #     frete = 0

        # CORRIGIDO:
        subtotal, desconto, frete = self._calcular_valores(tipo_cliente, uf)

        return round((subtotal - desconto + frete) * 100.0) / 100.0


    def gerar_relatorio(self):
        r = "=== RELATORIO DE VENDAS ===\n"
        vip = 0
        comum = 0
        func = 0
        for h in self.historico:
            partes = h.split("|")
            if partes[1] == "VIP":
                vip += 1
            elif partes[1] == "COMUM":
                comum += 1
            elif partes[1] == "FUNCIONARIO":
                func += 1
            r += partes[0] + " (" + partes[1] + "): R$ " + "%.2f" % float(partes[2]) + "\n"
        r += "Pedidos VIP: " + str(vip) + "\n"
        r += "Pedidos COMUM: " + str(comum) + "\n"
        r += "Pedidos FUNCIONARIO: " + str(func) + "\n"
        r += "Total vendido: R$ " + "%.2f" % self.total_vendido + "\n"
        if self.total_vendido > LIMITE_META_MENSAL:
            r += "Meta mensal atingida!\n"
        return r

    def verificar_estoque(self):
        alerta = ""
        for produto in self.estoque:
            if self.estoque[produto] < 5:
                alerta += ("ALERTA: " + produto + " com estoque baixo ("
                           + str(self.estoque[produto]) + ")\n")
                print("[EMAIL para compras@loja.com] Repor " + produto)
        return alerta

    def mensagem_promocional(self, tipo_cliente):
        if tipo_cliente == "VIP":
            return (
                f"Ofertas exclusivas: {DESCONTO_VIP:.0%} "
                f"em compras acima de R$ {LIMITE_DESCONTO}!"
            )
        elif tipo_cliente == "COMUM":
            return (
                f"Compre acima de R$ {LIMITE_DESCONTO} e ganhe "
                f"{DESCONTO_COMUM:.0%} de desconto!"
            )
        elif tipo_cliente == "FUNCIONARIO":
            return (
                f"Lembrete: seu desconto de "
                f"{DESCONTO_FUNCIONARIO:.0%} vale em toda a loja."
            )
        else:
            return ""