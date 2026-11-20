import java.util.HashMap;
import java.util.Scanner;
import java.util.Collections;

public class codeforces_637_A {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int n = scanner.nextInt();
        scanner.nextLine();
        String[] s = scanner.nextLine().split(" ");
        HashMap<String, Integer> w = new HashMap<>();

        for (String word : s) {
            w.put(word, w.getOrDefault(word, 0) + 1);
        }

        String a = "";
        int c = -1;

        for (int i = s.length - 1; i >= 0; i--) {
            String word = s[i];
            if (w.get(word) == Collections.max(w.values()) && (s.length - 1 - java.util.Arrays.asList(s).lastIndexOf(word)) > c) {
                a = word;
                c = s.length - 1 - java.util.Arrays.asList(s).lastIndexOf(word);
            }
        }

        System.out.println(a);
    }
}

// End of Code
