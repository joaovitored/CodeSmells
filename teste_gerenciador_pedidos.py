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

    def test_pedido_email_invalido(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10)

        resultado = self.gerenciador.processar_pedido(
            "Ana", "ana.email.com", "COMUM", "PIX", 1,
            "Rua A", "10", "Recife", "PE", "50000-000"
        )

        self.assertEqual(resultado, "ERRO: email invalido")

    def test_pedido_cep_invalido(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10)

        resultado = self.gerenciador.processar_pedido(
            "Ana", "ana@email.com", "COMUM", "PIX", 1,
            "Rua A", "10", "Recife", "PE", "123"
        )

        self.assertEqual(resultado, "ERRO: cep invalido")

    def test_pedido_produto_inexistente(self):
        self.gerenciador.adicionar_item("LAPIS", 2, 10)

        resultado = self.gerenciador.processar_pedido(
            "Ana", "ana@email.com", "COMUM", "PIX", 1,
            "Rua A", "10", "Recife", "PE", "50000-000"
        )

        self.assertEqual(resultado, "ERRO: produto inexistente LAPIS")

    def test_pedido_estoque_insuficiente(self):
        self.gerenciador.adicionar_item("CALCULADORA", 6, 50)

        resultado = self.gerenciador.processar_pedido(
            "Ana", "ana@email.com", "COMUM", "PIX", 1,
            "Rua A", "10", "Recife", "PE", "50000-000"
        )

        self.assertEqual(resultado, "ERRO: estoque insuficiente CALCULADORA")

    def test_pedido_com_erro_nao_altera_estoque_nem_itens(self):
        self.gerenciador.adicionar_item("CANETA", 2, 10)

        self.gerenciador.processar_pedido(
            "Ana", "ana.email.com", "COMUM", "PIX", 1,
            "Rua A", "10", "Recife", "PE", "50000-000"
        )

        self.assertEqual(self.gerenciador.estoque["CANETA"], 100)
        self.assertEqual(self.gerenciador.itens, [["CANETA", "2", "10"]])

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


if __name__ == "__main__":
    unittest.main()