import java.io.BufferedReader;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.NoSuchElementException;

/** Estoque CSV sem cabeçalho (codigo;quantidade), para uso local em uma instância. */
public class EstoqueArquivo {
    private final Path estoque;
    private final Path movimentacoes;
    private String ultimaMovimentacao = "";

    public EstoqueArquivo() {
        this(Path.of("estoque.csv"), Path.of("movimentacoes.txt"));
    }

    public EstoqueArquivo(Path estoque, Path movimentacoes) {
        this.estoque = estoque.toAbsolutePath().normalize();
        this.movimentacoes = movimentacoes.toAbsolutePath().normalize();
        if (this.estoque.equals(this.movimentacoes)) {
            throw new IllegalArgumentException("Arquivos devem ser distintos");
        }
    }

    private static void validarCodigo(String codigo) {
        if (codigo == null || !codigo.matches("[A-Za-z0-9_-]+")) {
            throw new IllegalArgumentException("Código inválido");
        }
    }

    // Valida o arquivo inteiro, inclusive linhas posteriores ao produto consultado.
    private Map<String, Integer> lerEstoque() throws IOException {
        Map<String, Integer> itens = new LinkedHashMap<>();
        try (BufferedReader leitor = Files.newBufferedReader(estoque, StandardCharsets.UTF_8)) {
            String linha;
            int numero = 0;
            while ((linha = leitor.readLine()) != null) {
                numero++;
                String[] campos = linha.split(";", -1);
                if (campos.length != 2) {
                    throw new IOException("Estrutura CSV inválida na linha " + numero);
                }
                try {
                    validarCodigo(campos[0]);
                    int quantidade = Integer.parseInt(campos[1]);
                    if (quantidade < 0 || itens.putIfAbsent(campos[0], quantidade) != null) {
                        throw new IllegalArgumentException("Quantidade negativa ou código duplicado");
                    }
                } catch (IllegalArgumentException e) {
                    throw new IOException("Registro inválido na linha " + numero, e);
                }
            }
        }
        return itens;
    }

    /** Retorna a quantidade, ou sinaliza produto ausente/erro de leitura. */
    public synchronized int consultarQuantidade(String codigo) {
        validarCodigo(codigo);
        try {
            Integer quantidade = lerEstoque().get(codigo);
            if (quantidade == null) throw new NoSuchElementException("Produto inexistente");
            return quantidade;
        } catch (IOException e) {
            throw new UncheckedIOException("Não foi possível consultar o estoque", e);
        }
    }

    /** Recusa ausência/insuficiência; entradas inválidas e erros de I/O são explícitos. */
    public synchronized boolean registrarSaida(String codigo, int quantidade) {
        validarCodigo(codigo);
        if (quantidade <= 0) throw new IllegalArgumentException("Quantidade deve ser positiva");
        try {
            Map<String, Integer> itens = lerEstoque();
            Integer disponivel = itens.get(codigo);
            if (disponivel == null || quantidade > disponivel) return false;
            itens.put(codigo, disponivel - quantidade);
            persistirSaida(itens, codigo, quantidade);
            ultimaMovimentacao = codigo;
            return true;
        } catch (IOException e) {
            throw new UncheckedIOException("Não foi possível registrar a saída", e);
        }
    }

    // Prepara o novo CSV antes de alterar o log; exige substituição atômica do CSV.
    // Se a escrita ou substituição falhar, tenta restaurar o tamanho anterior do log.
    // Não é uma transação ACID entre arquivos; pressupõe acesso exclusivo pela instância.
    private void persistirSaida(Map<String, Integer> itens, String codigo, int quantidade) throws IOException {
        Path temporario = Files.createTempFile(estoque.getParent(), "estoque-", ".tmp");
        try {
            StringBuilder csv = new StringBuilder();
            for (Map.Entry<String, Integer> item : itens.entrySet()) {
                csv.append(item.getKey()).append(';').append(item.getValue()).append('\n');
            }
            Files.writeString(temporario, csv, StandardCharsets.UTF_8);
            try (FileChannel log = FileChannel.open(movimentacoes, StandardOpenOption.CREATE,
                    StandardOpenOption.WRITE)) {
                long tamanhoAnterior = log.size();
                log.position(tamanhoAnterior);
                try {
                    ByteBuffer registro = StandardCharsets.UTF_8.encode(codigo + ";" + quantidade + "\n");
                    while (registro.hasRemaining()) log.write(registro);
                    log.force(true);
                    Files.move(temporario, estoque, StandardCopyOption.ATOMIC_MOVE,
                            StandardCopyOption.REPLACE_EXISTING);
                } catch (IOException e) {
                    try {
                        log.truncate(tamanhoAnterior);
                        log.force(true);
                    } catch (IOException rollback) {
                        e.addSuppressed(rollback);
                    }
                    throw e;
                }
            }
        } finally {
            Files.deleteIfExists(temporario);
        }
    }

    public synchronized String getUltimaMovimentacao() {
        return ultimaMovimentacao;
    }
}
