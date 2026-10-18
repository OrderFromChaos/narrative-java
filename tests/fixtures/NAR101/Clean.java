package fixtures.nar101;

/** Fixture for NAR101: a method above its first caller. */
public final class Clean {

    public static int total() {
        return base() + 1;
    }

    private static int base() {
        return 1;
    }
}
