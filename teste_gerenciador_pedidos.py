
import unittest
import os
import tempfile

from gerenciador_pedidos import GerenciadorPedidos


class TestGerenciadorPedidos(unittest.TestCase):

    def setUp(self):
        self.gerenciador = GerenciadorPedidos()
        self.pasta_original = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)

    def tearDown(self):
        os.chdir(self.pasta_original)
        self.temp_dir.cleanup()

    def test_estoque_inicial(self):
        self.assertEqual(self.gerenciador.estoque["CANETA"], 100)
        self.assertEqual(self.gerenciador.estoque["CADERNO"], 50)
        self.assertEqual(self.gerenciador.estoque["MOCHILA"], 10)
        self.assertEqual(self.gerenciador.estoque["CALCULADORA"], 5)

    def test_adicionar_item(self):
        self.gerenciador.adicionar_item("CANETA", 2, 3.50)

        self.assertEqual(
            self.gerenciador.itens,
            [["CANETA", "2", "3.5"]]
        )

    def test_pedido_sem_nome(self):
        resultado = self.gerenciador.processar_pedido(
            None, "teste@email.com", "COMUM", "PIX", 1,
            "Rua A", "10", "Recife", "PE", "50000-000"
        )

        self.assertEqual(resultado, "ERRO: cliente sem nome")

    def test_pedido_vazio(self):
        resultado = self.gerenciador.processar_pedido(
            "Ana", "ana@email.com", "COMUM", "PIX", 1,
            "Rua A", "10", "Recife", "PE", "50000-000"
        )

        self.assertEqual(resultado, "ERRO: pedido vazio")

    def test_orcamento_vip(self):
        self.gerenciador.adicionar_item("CANETA", 10, 10)

        resultado = self.gerenciador.calcular_orcamento(
            "VIP", "PE"
        )

        self.assertEqual(resultado, 90.0)

    def test_pedido_confirmado_atualiza_estado(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10)

        resultado = self.gerenciador.processar_pedido(
            "Ana", "ana@email.com", "COMUM", "PIX", 1,
            "Rua A", "10", "Recife", "PE", "50000-000"
        )

        self.assertEqual(resultado, "OK: 30.88")
        self.assertEqual(self.gerenciador.estoque["CANETA"], 98)
        self.assertEqual(self.gerenciador.itens, [])
        self.assertAlmostEqual(self.gerenciador.total_vendido, 30.88)
        self.assertTrue(os.path.exists("pedidos.csv"))

        with open("pedidos.csv", encoding="utf-8") as arquivo:
            conteudo = arquivo.read()

        self.assertIn("Ana;ana@email.com;COMUM;PIX;30.88;", conteudo)

    def test_desconto_vip_abaixo_de_500(self):
        self.gerenciador.adicionar_item("CANETA", 10, 10.0) # Subtotal: 100.0 (< 500)
        # 100 - 10% Desconto VIP Minimo (10.0) = 90.0. Frete VIP = 0. PIX aplica 5% s/ 90 = 85.50
        resultado = self.gerenciador.processar_pedido(
            "Carla", "carla@email.com", "VIP", "PIX", 1, 
            "Rua C", "10", "Recife", "PE", "50000-000"
        )
        self.assertEqual(resultado, "OK: 85.50")

    def test_desconto_funcionario(self):
        self.gerenciador.adicionar_item("CANETA", 10, 10.0) # Subtotal: 100.0
        # 100 - 20% Colaborador (20.0) = 80.0. Frete PE = 12.50. Total parcial = 92.50. PIX aplica 5% s/ 92.50 = 87.875 -> 87.88
        resultado = self.gerenciador.processar_pedido(
            "Dani", "dani@email.com", "FUNCIONARIO", "PIX", 1, 
            "Rua D", "10", "Recife", "PE", "50000-000"
        )
        self.assertEqual(resultado, "OK: 87.88")

    def test_desconto_comum_acima_de_500(self):
        self.gerenciador.adicionar_item("CADERNO", 10, 60.0) # Subtotal: 600.0 (> 500)
        # 600 - 5% Comum (30.0) = 570.0. Como 570 > 300, ganha frete grátis. PIX aplica 5% s/ 570 = 541.50
        resultado = self.gerenciador.processar_pedido(
            "Beto", "beto@email.com", "COMUM", "PIX", 1, 
            "Rua B", "10", "Recife", "PE", "50000-000"
        )
        self.assertEqual(resultado, "OK: 541.50")

    def test_frete_nordeste_outros_estados(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10.0) # Subtotal: 20.0
        # 20.0 + 22.90 Frete Nordeste (RN) = 42.90. PIX aplica 5% s/ 42.90 = 40.755 -> 40.76
        resultado = self.gerenciador.processar_pedido(
            "Fabio", "fabio@email.com", "COMUM", "PIX", 1, 
            "Rua F", "10", "Natal", "RN", "59000-000"
        )
        self.assertEqual(resultado, "OK: 40.75")

    def test_frete_outras_regioes(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10.0) # Subtotal: 20.0
        # 20.0 + 39.90 Frete Outras Regiões (SP) = 59.90. PIX aplica 5% s/ 59.90 = 56.905 -> 56.91
        resultado = self.gerenciador.processar_pedido(
            "Gabi", "gabi@email.com", "COMUM", "PIX", 1, 
            "Rua G", "10", "Sao Paulo", "SP", "01000-000"
        )
        self.assertEqual(resultado, "OK: 56.90")

    def test_frete_gratis_por_valor_liquido_acima_300(self):
        self.gerenciador.adicionar_item("CADERNO", 8, 50.0) # Subtotal: 400.0. Sem desconto comum (< 500)
        # Líquido (400) > 300 limite frete grátis -> Frete = 0. PIX aplica 5% s/ 400 = 380.00
        resultado = self.gerenciador.processar_pedido(
            "Hugo", "hugo@email.com", "COMUM", "PIX", 1, 
            "Rua H", "10", "Sao Paulo", "SP", "01000-000"
        )
        self.assertEqual(resultado, "OK: 380.00")

    def test_pagamento_boleto_soma_taxa(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10.0) # Subtotal: 20.0
        # 20.0 + 12.50 Frete PE = 32.50. BOLETO soma taxa de 2.50 = 35.00
        resultado = self.gerenciador.processar_pedido(
            "Lia", "lia@email.com", "COMUM", "BOLETO", 1, 
            "Rua L", "10", "Recife", "PE", "50000-000"
        )
        self.assertEqual(resultado, "OK: 35.00")

    def test_pagamento_cartao_ate_3x_sem_juros(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10.0) # Subtotal: 20.0
        # 20.0 + 12.50 Frete PE = 32.50. No cartão em 3x não deve cobrar juros extras.
        resultado = self.gerenciador.processar_pedido(
            "Lia", "lia@email.com", "COMUM", "CARTAO", 3, 
            "Rua L", "10", "Recife", "PE", "50000-000"
        )
        self.assertEqual(resultado, "OK: 32.50")

    def test_pagamento_cartao_com_juros_4x(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10.0) # Subtotal: 20.0
        # Base: 20.0 + 12.50 Frete PE = 32.50. 4 parcelas aplica juros: 32.50 * (1 + 0.0199 * 4) = 35.087 -> 35.09
        resultado = self.gerenciador.processar_pedido(
            "Lia", "lia@email.com", "COMUM", "CARTAO", 4, 
            "Rua L", "10", "Recife", "PE", "50000-000"
        )
        self.assertEqual(resultado, "OK: 35.09")

    def test_pagamento_cartao_parcelas_invalidas_altas(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10.0)
        resultado = self.gerenciador.processar_pedido(
            "Lia", "lia@email.com", "COMUM", "CARTAO", 13, 
            "Rua L", "10", "Recife", "PE", "50000-000"
        )
        self.assertEqual(resultado, "ERRO: parcelas invalidas")

    def test_forma_pagamento_invalida(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10.0)
        resultado = self.gerenciador.processar_pedido(
            "Lia", "lia@email.com", "COMUM", "CHEQUE", 1, 
            "Rua L", "10", "Recife", "PE", "50000-000"
        )
        self.assertEqual(resultado, "ERRO: forma de pagamento invalida")

    def test_erro_email_invalido(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10.0)
        resultado = self.gerenciador.processar_pedido(
            "Marta", "marta_email_invalido.com", "COMUM", "PIX", 1, 
            "Rua M", "10", "Recife", "PE", "50000-000"
        )
        self.assertEqual(resultado, "ERRO: email invalido")

    def test_erro_cep_invalido(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10.0)
        resultado = self.gerenciador.processar_pedido(
            "Neto", "neto@email.com", "COMUM", "PIX", 1, 
            "Rua N", "10", "Recife", "PE", "123"
        )
        self.assertEqual(resultado, "ERRO: cep invalido")

    def test_erro_produto_inexistente(self):
        self.gerenciador.adicionar_item("LAPIS_MAGICO", 1, 5.0)
        resultado = self.gerenciador.processar_pedido(
            "Oscar", "oscar@email.com", "COMUM", "PIX", 1, 
            "Rua O", "10", "Recife", "PE", "50000-000"
        )
        self.assertEqual(resultado, "ERRO: produto inexistente LAPIS_MAGICO")

    def test_erro_estoque_insuficiente(self):
        self.gerenciador.adicionar_item("MOCHILA", 11, 100.0) 
        resultado = self.gerenciador.processar_pedido(
            "Paula", "paula@email.com", "COMUM", "PIX", 1, 
            "Rua P", "10", "Recife", "PE", "50000-000"
        )
        self.assertEqual(resultado, "ERRO: estoque insuficiente MOCHILA")

    def test_erro_tipo_cliente_desconhecido(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10.0)
        resultado = self.gerenciador.processar_pedido(
            "Rui", "rui@email.com", "INVALIDO", "PIX", 1, 
            "Rua R", "10", "Recife", "PE", "50000-000"
        )
        self.assertEqual(resultado, "ERRO: tipo de cliente desconhecido")

    def test_gerar_relatorio_formato(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10.0)
        self.gerenciador.processar_pedido(
            "Ana", "ana@email.com", "COMUM", "PIX", 1, 
            "Rua A", "10", "Recife", "PE", "50000-000"
        )
        relatorio = self.gerenciador.gerar_relatorio()
        self.assertIn("=== RELATORIO DE VENDAS ===", relatorio)
        self.assertIn("Total vendido: R$ 30.88", relatorio)

    def test_verificar_estoque_alerta(self):
        # Altera manualmente o estoque para simular nível baixo (< 5)
        self.gerenciador.estoque["MOCHILA"] = 4
        alerta = self.gerenciador.verificar_estoque()
        self.assertIn("ALERTA: MOCHILA com estoque baixo", alerta)

    def test_mensagem_promocional_comum_e_vip(self):
        msg_vip = self.gerenciador.mensagem_promocional("VIP")
        msg_comum = self.gerenciador.mensagem_promocional("COMUM")
        self.assertIn("Ofertas exclusivas", msg_vip)
        self.assertIn("ganhe 5%", msg_comum)

    def test_caracterizacao_bug_maranhao_ma(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10.0) # Subtotal: 20.0
        
        orcamento = self.gerenciador.calcular_orcamento("COMUM", "MA")
        self.assertEqual(orcamento, 59.90)
        
        processado = self.gerenciador.processar_pedido(
            "Ze", "ze@email.com", "COMUM", "PIX", 1, 
            "Rua X", "1", "Sao Luis", "MA", "65000-000"
        )
        self.assertEqual(processado, "OK: 40.75")


if __name__ == "__main__":
    unittest.main()
