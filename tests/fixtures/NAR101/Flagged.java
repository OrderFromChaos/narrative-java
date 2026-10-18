package fixtures.nar101;

/** Fixture for NAR101: a method above its first caller. */
public final class Flagged {

    private static int base() {
        return 1;
    }

    public static int total() {
        return base() + 1;
    }
}
