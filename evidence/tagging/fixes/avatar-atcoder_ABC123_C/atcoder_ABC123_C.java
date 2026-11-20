import java.util.Scanner;
import java.util.Arrays;

public class atcoder_ABC123_C {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        long N = scanner.nextLong();
        long[] A = new long[5];
        for (int i = 0; i < 5; i++) {
            A[i] = scanner.nextLong();
        }
        
        long minA = Arrays.stream(A).min().getAsLong();
        System.out.println((long) Math.ceil((double) N / minA) + 4);
    }
}
// End of Code
