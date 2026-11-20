import java.util.Arrays;
import java.util.Scanner;

public class atcoder_ABC143_D {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int n = scanner.nextInt();
        int[] l = new int[n];
        for (int i = 0; i < n; i++) {
            l[i] = scanner.nextInt();
        }
        scanner.close();

        Arrays.sort(l);
        long ans = 0;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                int a = l[i];
                int b = l[j];
                int right = lowerBound(l, a + b);
                int left = upperBound(l, Math.max(a - b, b - a));
                int tmp = Math.max(0, right - left);
                if (left <= i && i < right) {
                    tmp -= 1;
                }
                if (left <= j && j < right) {
                    tmp -= 1;
                }
                ans += tmp;
            }
        }
        System.out.println(ans / 3);
    }
    static int lowerBound(int[] x,int v){int lo=0,hi=x.length;while(lo<hi){int m=(lo+hi)>>>1;if(x[m]<v)lo=m+1;else hi=m;}return lo;}
    static int upperBound(int[] x,int v){int lo=0,hi=x.length;while(lo<hi){int m=(lo+hi)>>>1;if(x[m]<=v)lo=m+1;else hi=m;}return lo;}
}
// End of Code
