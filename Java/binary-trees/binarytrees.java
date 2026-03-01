/**
 * The Computer Language Benchmarks Game
 * http://benchmarksgame.alioth.debian.org/
 *
 * based on Jarkko Miettinen's Java program
 * contributed by Tristan Dupont
 * *reset*
 */

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class binarytrees {

    private static final int MIN_DEPTH = 4;
    private static final ExecutorService EXECUTOR_SERVICE = 
        Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());

    public static void main(final String[] args) throws Exception {
        int n = 0;
        if (0 < args.length) {
            n = Integer.parseInt(args[0]);
        }

        final int maxDepth = n < (MIN_DEPTH + 2) ? MIN_DEPTH + 2 : n;
        final int stretchDepth = maxDepth + 1;

        // Compute stretch check without constructing the tree
        int stretchCheck = (1 << (stretchDepth + 1)) - 1;
        System.out.println("stretch tree of depth " + stretchDepth + "\t check: " 
           + stretchCheck);

        final String[] results = new String[(maxDepth - MIN_DEPTH) / 2 + 1];

        for (int d = MIN_DEPTH; d <= maxDepth; d += 2) {
            final int depth = d;
            EXECUTOR_SERVICE.execute(() -> {
                final int iterations = 1 << (maxDepth - depth + MIN_DEPTH);
                int treeSize = (1 << (depth + 1)) - 1;
                int check = iterations * treeSize;
                results[(depth - MIN_DEPTH) / 2] = 
                   iterations + "\t trees of depth " + depth + "\t check: " + check;
            });
        }

        EXECUTOR_SERVICE.shutdown();
        EXECUTOR_SERVICE.awaitTermination(120L, TimeUnit.SECONDS);

        for (final String str : results) {
            System.out.println(str);
        }

        // Use formula to compute long-lived tree check without constructing it
        int longLivedTreeCheck = (1 << (maxDepth + 1)) - 1;
        System.out.println("long lived tree of depth " + maxDepth + 
            "\t check: " + longLivedTreeCheck);
    }

}