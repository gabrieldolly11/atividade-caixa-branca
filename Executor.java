/** Executa a mesma interface pública nas duas versões, sem dependências externas. */
public class Executor {
    public static void main(String[] args) {
        EstoqueArquivo estoque = new EstoqueArquivo();
        for (String comando : args) {
            String[] partes = comando.split(":", -1);
            String codigo = partes.length > 1 && partes[1].equals("<null>") ? null :
                partes.length > 1 ? partes[1] : "";
            try {
                switch (partes[0]) {
                    case "Q": System.out.println("Q=" + estoque.consultarQuantidade(codigo)); break;
                    case "R": System.out.println("R=" + estoque.registrarSaida(codigo, Integer.parseInt(partes[2]))); break;
                    case "U": System.out.println("U=" + estoque.getUltimaMovimentacao()); break;
                    default: throw new IllegalArgumentException("Comando desconhecido");
                }
            } catch (RuntimeException e) {
                System.out.println("EX=" + e.getClass().getSimpleName());
            }
        }
    }
}
