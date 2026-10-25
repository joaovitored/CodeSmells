## 1. Code smells identificados


| Code smell | Evidência no código original | Consequência |  |
|---|---|---|---|
| **God Class** | `GerenciadorPedidos` valida entradas, calcula preços, atualiza estoque, grava CSV, imprime notificações e gera relatórios | Muitas responsabilidades ficam concentradas na mesma classe. 
| **Long Method** | `processar_pedido()` executa validação, cálculo, pagamento, estoque, persistência e confirmação | O método fica difícil de entender, testar e modificar. 
| **Duplicated Code** | Cálculos de subtotal, desconto e frete aparecem em `processar_pedido()` e `calcular_orcamento()` | As regras podem divergir quando são alteradas. 
| **Magic Numbers** | `500`, `300`, `0.05`, `0.15`, `12.5`, `22.9`, `39.9`, `0.0199` | As regras de negócio ficam pouco explícitas e mais difíceis de manter. | 
| **Primitive Obsession** | Strings como `"VIP"`, `"COMUM"`, `"PIX"`, `"CARTAO"` e registros concatenados com `| `.
| **Divergent Change** | A mesma classe precisaria mudar para alterar preço, CSV, notificação, estoque ou relatório | Mudanças de naturezas diferentes ficam concentradas na mesma classe.
| **Side Effects** | `processar_pedido()` grava arquivo e imprime mensagens; `verificar_estoque()` também imprime | Os métodos misturam processamento com efeitos externos, dificultando testes isolados. 
| **Inconsistent Business Rules** | `MA` tem frete regional em `processar_pedido()`, mas não em `calcular_orcamento()` | O orçamento e o processamento podem apresentar valores diferentes para a mesma UF.
| **Inconsistent Validation** | `processar_pedido()` rejeita tipo de cliente desconhecido; `calcular_orcamento()` não faz a mesma validação | A mesma entrada pode ser tratada de maneira diferente entre operações.

para realizar a bateria de testes do script teste_gerenciador_pedidos, use python -m unittest -v no terminal


## 2. Testes de caracterização

Os testes estão em `teste_gerenciador_pedidos.py`, com 11 cenários que registram o comportamento atual da classe:

*   **Estado inicial:** Estoque inicial dos produtos e adição de item ao pedido.
*   **Erros e validações:** Pedido sem nome, pedido vazio, e-mail inválido, CEP inválido, produto inexistente e estoque insuficiente.
*   **Pedido com erro:** Um pedido rejeitado não altera o estoque nem os itens.
*   **Orçamento:** Cálculo do orçamento para cliente VIP.
*   **Pedido confirmado:** Atualiza estoque, itens e total vendido, e grava o `pedidos.csv`.

Pendente: descontos, fretes, formas de pagamento, relatório, alerta de estoque, mensagem promocional e o bug do `MA`.


## 3. Histórico de refatoração e commits

### Refatoração 1 — Extração de constantes
* **Code smell tratado:** Magic Numbers.

* **O que mudou:** Os valores numéricos associados às regras de desconto, frete, pagamento, parcelamento e meta mensal foram substituídos por constantes nomeadas. As mensagens promocionais também passaram a utilizar essas constantes.

* **Testes:** os seis testes de caracterização continuaram passando após a alteração.

* **Princípio SOLID:** a extração de constantes melhora a legibilidade e a manutenção, mas não restaura diretamente um princípio SOLID específico.

* **Commit:** extrai constantes comerciais.

### Refatoração 2 — Separação da validação do pedido

*   **Code smell tratado:** Long Method.

*   **O que mudou:** A validação de nome, e-mail, pedido vazio, CEP, produto e estoque saiu de `processar_pedido()` e foi para o método `_validar_pedido()`.A ordem das verificações foi mantida, então as mensagens de erro não mudam.

*   **Testes:** Foram adicionados testes para e-mail inválido, CEP inválido, produto inexistente, estoque insuficiente e pedido com erro que não altera estoque nem itens. Os onze testes de caracterização continuaram passando após a alteração.

*   **Princípio SOLID:** SRP. `processar_pedido()` deixa de ser responsável por validar o pedido.

*   **Commit:** `extrai validação do pedido (Long Method)`


### Refatoração 3 — Eliminação de Código Duplicado (Cálculo de Preço)
* **Code smell tratado:** Duplicated Code (e Inconsistent Business Rules).

* **O que mudou:** Toda a lógica repetida que calculava o subtotal, os descontos por categoria e o frete regional foi extraída dos métodos `processar_pedido()` e `calcular_orcamento()` e centralizada em um único método privado chamado `_calcular_valores()`. O código antigo foi mantido comentado para fins de rastreabilidade. Com essa unificação, o bug de omissão da UF "MA" no orçamento foi corrigido automaticamente.

* **Testes:** O teste de caracterização do bug do MA foi atualizado para validar a correção da inconsistência (agora ambos os fluxos retornam R$ 32.90 de frete). Toda a bateria de testes continuou passando com sucesso (verde).

* **Princípio SOLID:** SRP (Single Responsibility Principle). A classe agora possui um único ponto isolado e especializado responsável por computar as regras de precificação financeira.

* **Commit:** `remove código duplicado e unifica regras de preço (DRY/SRP)`

### Refatoração 4 — Padrão Strategy para Descontos de Clientes
* **Code smell tratado:** Primitive Obsession (Uso de strings estruturais em cadeias de if/elif).

* **O que mudou:** As regras de desconto baseadas no tipo de cliente foram extraídas de dentro de condicionais do método `_calcular_valores()` e transformadas em classes de estratégia isoladas (`DescontoComum`, `DescontoVIP`, `DescontoFuncionario`). O `GerenciadorPedidos` agora resolve dinamicamente qual regra aplicar através de um mapa de estratégias no construtor.

* **Testes:** Toda a bateria de testes de caracterização de descontos (VIP acima/abaixo, funcionário e comum) passou com sucesso (verde).

* **Princípio SOLID:** OCP (Open/Closed Principle). O sistema agora está fechado para modificação no método de cálculo, mas aberto para expansão. Se um novo tipo de cliente for criado, basta criar sua classe de estratégia e registrá-la no dicionário, sem tocar na lógica central.

* **Commit:** `aplica padrão Strategy para descontos de clientes (OCP)`

### Refatoração 5 — Padrão Strategy para Formas de Pagamento
* **Code smell tratado:** Primitive Obsession (Condicionais baseadas em strings de pagamento).

* **O que mudou:** A lógica de cálculo de taxas, juros e validações de parcelas das formas de pagamento foi movida de dentro do método `processar_pedido()` para classes dedicadas (`PagamentoPIX`, `PagamentoBoleto`, `PagamentoCartao`). O gerenciador agora resolve o fluxo financeiro delegando a execução para a estratégia correspondente através de um mapa chave-valor.

* **Testes:** Toda a bateria de testes cobrindo PIX, Boleto, Cartão em 3x, Cartão em 5x com juros e erros de parcelamento continuou passando com 100% de sucesso (verde).

* **Princípio SOLID:** OCP (Open/Closed Principle). O método central de processamento de pedidos está protegido contra alterações caso novas formas de pagamento (como criptomoedas ou vale-refeição) sejam adicionadas no futuro; bastará implementar uma nova classe e registrá-la.

* **Commit:** `aplica padrão Strategy para formas de pagamento (OCP)`


## 4. Qual princípio SOLID utilizado?
