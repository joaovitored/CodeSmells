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


## 3. Histórico de refatoração e commits


Refatoração 1 — Extração de constantes

Code smell tratado: Magic Numbers.

Os valores numéricos associados às regras de desconto, frete, pagamento, parcelamento e meta mensal foram substituídos por constantes nomeadas. As mensagens promocionais também passaram a utilizar essas constantes.

Testes: os seis testes de caracterização continuaram passando após a alteração.

Princípio SOLID: a extração de constantes melhora a legibilidade e a manutenção, mas não restaura diretamente um princípio SOLID específico.

Commit: extrai constantes comerciais.