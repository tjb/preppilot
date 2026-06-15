# lessons.py — iOS interview-prep lesson content (keyed by week number 1–12)

LESSONS: dict[int, dict] = {
    1: {
        "overview": "Value vs reference semantics is the first thing senior iOS interviewers probe because it underpins every architecture decision — from why SwiftUI models are structs to why shared mutable state causes bugs. Staff-level candidates are expected to explain Copy-on-Write, articulate the tradeoffs, and catch subtle gotchas like structs that contain classes.",
        "concepts": [
            {
                "title": "Value types copy on assignment",
                "body": "Structs, enums, and tuples are value types: assignment produces an independent copy. Changes to the copy never affect the original. This makes reasoning about state trivial because a value you hold can never be mutated by another part of the program behind your back.",
                "code": """struct Point { var x: Int; var y: Int }

var a = Point(x: 0, y: 0)
var b = a       // full copy
b.x = 99

print(a.x)      // 0 — a is unchanged
print(b.x)      // 99""",
                "tip": "Interviewers often ask 'what makes a type a value type?' The answer is copy semantics on assignment, not the keyword struct. Tuples and enums are also value types. Follow-up: 'Can a struct ever behave like a reference type?' — yes, if it wraps a class (the hybrid gotcha)."
            },
            {
                "title": "Reference types share identity: === vs ==",
                "body": "Classes are reference types: assignment copies the pointer, not the object. Two variables can refer to the same instance, so mutation via one variable is visible through the other. Use === to test pointer equality (same instance) and == to test value equality (same logical content).",
                "code": """class Counter {
    var count = 0
}

let c1 = Counter()
let c2 = c1         // both point to the same object

c2.count = 10
print(c1.count)     // 10 — shared mutation

print(c1 === c2)    // true  — same instance
print(c1 === Counter())  // false — different instance""",
                "tip": "A common wrong answer is saying 'classes use == for identity.' === is the identity operator. Interviewers may ask you to implement == on a class — that requires conforming to Equatable and is distinct from identity."
            },
            {
                "title": "Copy-on-Write (CoW) in stdlib collections",
                "body": "Swift arrays, dictionaries, and sets appear to copy on assignment but defer the actual copy until a mutation occurs. This makes passing large collections cheap. You can implement CoW in your own types using isKnownUniquelyReferenced to check whether the backing storage is shared before mutating.",
                "code": """final class Storage {
    var values: [Int]
    init(_ values: [Int]) { self.values = values }
}

struct CoWArray {
    private var storage = Storage([])

    mutating func append(_ value: Int) {
        // Only copy the backing store if someone else holds a reference.
        if !isKnownUniquelyReferenced(&storage) {
            storage = Storage(storage.values)
        }
        storage.values.append(value)
    }

    var count: Int { storage.values.count }
}""",
                "tip": "Staff-level candidates are expected to know that stdlib collections are NOT naively copied on assignment. The follow-up is always 'how would you implement CoW yourself?' — isKnownUniquelyReferenced is the answer. Note it only works with final classes."
            },
            {
                "title": "Mutability rules: let on class vs struct",
                "body": "On a struct, let makes the entire value immutable — you cannot call any mutating methods. On a class, let only makes the reference constant (you cannot reassign it to a different object), but the object's properties are still mutable if they are declared var. This asymmetry trips up candidates.",
                "code": """struct Rect { var width: Double; var height: Double }
let r = Rect(width: 10, height: 20)
// r.width = 99   // compile error — struct is fully immutable under let

class Box { var width: Double; init(_ w: Double) { width = w } }
let b = Box(5)
b.width = 99    // fine — let only locks the reference, not the properties
// b = Box(10)  // compile error — cannot rebind let""",
                "tip": "This is a classic gotcha question. The expected answer is: 'let on a struct freezes the entire value; let on a class only freezes the pointer.' Interviewers probe whether you understand that Swift's mutability model for value types is enforced by the compiler at the variable level, not through access control."
            },
            {
                "title": "Choosing struct vs class — Apple's guidance and the hybrid gotcha",
                "body": "Apple's guidance is to default to structs unless you need identity, Objective-C interop, or reference semantics intentionally. The dangerous middle ground is a struct that contains a class property: the struct copies on assignment but the contained class is still shared, so mutations to the class are visible across all copies.",
                "code": """class ImageData { var pixels: [UInt8] = [] }

struct ImageView {
    var frame: CGRect
    var data: ImageData   // ← class inside struct
}

var view1 = ImageView(frame: .zero, data: ImageData())
var view2 = view1           // struct copies frame, but data is shared

view2.data.pixels = [0xFF]
print(view1.data.pixels)    // [255] — shared! Struct gave false safety.""",
                "tip": "The hybrid struct/class scenario is the most common senior gotcha on this topic. The fix is either to make ImageData a struct (if small) or to implement proper CoW wrapping. Interviewers use this to separate candidates who have memorized 'use structs' from those who truly understand the memory model."
            },
        ],
        "try_it": [
            "In a Swift playground, create a struct with a var array property. Assign it to a second variable, mutate the array on the copy, then verify the original is unchanged using print. Then repeat with a class to observe shared mutation.",
            "Implement a simple CoWBuffer struct backed by a final class that stores [Double]. Add a mutating append method that calls isKnownUniquelyReferenced before deciding whether to copy. Write a test that proves two CoWBuffer variables diverge after mutation.",
            "Write a struct PersonRecord containing a class-based Address. Assign to a copy, mutate the address on the copy, and observe the shared-state bug. Then fix it by converting Address to a struct and confirming independence.",
            "Open any SwiftUI project and find a model type that is a class. Ask: what would break if it were a struct? What would improve? Practice articulating the tradeoffs aloud as you would in an interview."
        ]
    },
    2: {
        "overview": "ARC is the memory management mechanism every iOS app relies on. Senior interviewers probe retain cycles because they are the most common source of subtle memory leaks in real apps. Staff candidates must be able to diagnose cycles, choose correctly between weak and unowned, and demonstrate how to write tests that catch leaks before they ship.",
        "concepts": [
            {
                "title": "How ARC works: retain count and deterministic deallocation",
                "body": "ARC inserts retain and release calls at compile time. Each strong reference increments the retain count; when it reaches zero the object is immediately deallocated. Unlike garbage collection there is no background sweep — deallocation is deterministic and happens at the exact point the last strong reference is released.",
                "code": """class NetworkSession {
    init() { print("Session created") }
    deinit { print("Session deallocated") }  // called deterministically
}

func makeRequest() {
    let session = NetworkSession()  // retain count: 1
    // ... use session
}   // session goes out of scope → retain count 0 → deinit called immediately""",
                "tip": "Interviewers distinguish ARC from GC by asking about determinism. Key points: ARC is compile-time, not runtime; deinit is called immediately at count=0; there is no 'collection pause.' A common wrong answer is 'ARC uses a garbage collector under the hood' — it does not."
            },
            {
                "title": "Retain cycles: the Person/Apartment example",
                "body": "A retain cycle occurs when two objects hold strong references to each other, preventing either retain count from ever reaching zero. Neither object is ever deallocated even after all external references are released. This is the primary cause of memory leaks in iOS apps.",
                "code": """class Person {
    let name: String
    var apartment: Apartment?
    init(name: String) { self.name = name }
    deinit { print("\\(name) deallocated") }
}

class Apartment {
    let unit: String
    var tenant: Person?       // strong → cycle!
    init(unit: String) { self.unit = unit }
    deinit { print("Apt \\(unit) deallocated") }
}

var alice: Person? = Person(name: "Alice")
var apt: Apartment? = Apartment(unit: "4B")
alice?.apartment = apt
apt?.tenant = alice          // cycle formed

alice = nil                  // deinit NOT called — cycle keeps both alive
apt = nil                    // deinit NOT called""",
                "tip": "This exact example appears in Apple's Swift docs and interviewers use it verbatim. Know it cold. The follow-up is always 'how do you break the cycle?' — make one side weak. The question 'which side should be weak?' tests domain knowledge: the object with the shorter or dependent lifetime becomes weak."
            },
            {
                "title": "weak vs unowned: when each is correct",
                "body": "weak references are always Optional and are automatically set to nil when the referenced object is deallocated — use weak when the referenced object can legitimately outlive the reference holder or be nil. unowned references are non-Optional and are never zeroed — use unowned only when you are certain the referenced object will always outlive the reference, otherwise you get a crash.",
                "code": """class Owner {
    var asset: Asset?
}

class Asset {
    // Owner could be released before Asset in some flows → weak is safer
    weak var owner: Owner?

    // formatString will always outlive this closure → unowned is correct here
    let describe: () -> String
    init(name: String) {
        let label = name           // capture value type — no retain needed
        describe = { "Asset: \\(label)" }
    }
}""",
                "tip": "The interview trap is 'can I always use weak instead of unowned to be safe?' Technically yes, but unowned signals a stronger contract and avoids forced unwrapping in code that uses the reference. Interviewers probe whether you know the crash scenario for unowned: accessing it after the target is deallocated gives an immediate crash, not a nil deref."
            },
            {
                "title": "Capture lists in closures: [weak self] and the guard-let idiom",
                "body": "Closures capture surrounding variables strongly by default. When a closure is stored on self (as a completion handler or property), a retain cycle forms: self → closure → self. Breaking it requires capturing self weakly in a capture list, then guarding against nil before use inside the closure.",
                "code": """class FeedViewModel {
    private var cancellable: Task<Void, Never>?

    func loadFeed() {
        cancellable = Task { [weak self] in
            guard let self else { return }   // Swift 5.3+ shorthand
            let items = await FeedService.fetch()
            self.handle(items)
        }
    }

    private func handle(_ items: [Item]) { /* update state */ }
    deinit { cancellable?.cancel() }
}""",
                "tip": "The most common mistake candidates make is using [unowned self] in completion handlers because 'it avoids the optional.' This crashes if the view model is released before the network call returns. Always use [weak self] for async callbacks. The follow-up: 'When would [unowned self] be correct in a closure?' — only when the closure cannot outlive self (e.g., map/filter on a local collection)."
            },
            {
                "title": "Testing for leaks: the weak var + nil + XCTAssertNil pattern",
                "body": "You can write deterministic memory leak tests without Instruments. Allocate the object under test, hold a weak reference to it, release all strong references, and then assert the weak reference is nil. If a cycle exists the object survives and the assertion fails, catching the leak in CI.",
                "code": """import XCTest
@testable import MyApp

final class FeedViewModelLeakTests: XCTestCase {
    func test_viewModel_isReleasedAfterLoadCompletes() async throws {
        weak var weakSut: FeedViewModel?

        try await Task {
            let sut = FeedViewModel(service: MockFeedService())
            weakSut = sut
            await sut.loadFeed()
        }.value

        // If a retain cycle exists, weakSut will still be non-nil here.
        XCTAssertNil(weakSut, "FeedViewModel leaked — likely a retain cycle")
    }
}""",
                "tip": "This pattern is underused and impresses interviewers because it shows you think about memory proactively, not just reactively with Instruments. The key mechanic is that weak references are zeroed immediately at dealloc, making this test perfectly deterministic with ARC. Staff candidates should be able to write this from memory."
            },
        ],
        "try_it": [
            "Reproduce the Person/Apartment retain cycle in a playground. Observe that deinit is never printed. Then break the cycle by making tenant weak and confirm both deinit messages appear.",
            "Add a deinit with a print statement to a ViewModel in your project. Navigate away and back, and check the console. If deinit never fires, use the Memory Graph Debugger in Xcode to find the cycle (Debug > Memory Graph).",
            "Write a leak test using the weak-var-nil pattern for a ViewModel that takes a closure-based service dependency. Intentionally create a cycle (strong capture of self in the stored closure) to make the test fail, then fix it with [weak self].",
            "Search your codebase for completion handlers. For each one that captures self, verify the capture list is [weak self] and that there is a guard let self pattern before use."
        ]
    },
    3: {
        "overview": "Swift Concurrency replaced GCD for most new code and is the primary concurrency topic at senior/staff iOS interviews. Interviewers probe whether candidates understand that async/await is not just syntax sugar over threads, how actors enforce isolation without locks, and how Sendable prevents data races at compile time.",
        "concepts": [
            {
                "title": "async/await basics: suspension points and the cooperative thread pool",
                "body": "await marks a suspension point where the current task yields execution back to the runtime without blocking its underlying thread. The runtime uses a cooperative thread pool sized to available CPU cores — not one thread per task. This means thousands of concurrent tasks can exist without thousands of threads.",
                "code": """func fetchUser(id: UUID) async throws -> User {
    // Suspension point: thread is freed while waiting for network
    let (data, response) = try await URLSession.shared.data(from: userURL(id))
    guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
        throw APIError.badStatus
    }
    return try JSONDecoder().decode(User.self, from: data)
}

// Call site — must be in async context
func loadProfile() async {
    do {
        let user = try await fetchUser(id: currentUserID)
        updateUI(with: user)
    } catch {
        showError(error)
    }
}""",
                "tip": "Interviewers listen for whether you say 'await blocks the thread' — that is wrong and a red flag. The correct answer is 'await suspends the task and frees the thread to do other work.' This distinction is exactly why Swift Concurrency scales better than one-thread-per-operation models."
            },
            {
                "title": "Task vs Task.detached: actor context inheritance",
                "body": "Task inherits the actor context of its creator — a Task created inside a @MainActor method runs its synchronous portions on the main actor. Task.detached explicitly creates a task with no actor context, running on the cooperative pool. Use Task when you want to stay on the current actor; use Task.detached sparingly when you need to intentionally escape the current actor.",
                "code": """@MainActor
class ProfileViewModel {
    func refresh() {
        // Inherits @MainActor — synchronous work stays on main actor
        Task {
            let user = try? await fetchUser()   // suspends, frees main actor
            self.user = user                    // back on main actor after await
        }

        // Explicitly NOT on main actor — no actor context inherited
        Task.detached(priority: .background) {
            await self.processThumbnails()      // runs on cooperative pool
        }
    }
}""",
                "tip": "The follow-up question is almost always: 'Why not always use Task.detached?' The answer is that Task.detached loses the actor context, so you must manually hop back to the main actor (await MainActor.run { }) to update UI. Task inheritance is a convenience that prevents this mistake."
            },
            {
                "title": "Actor isolation: serialized access and awaiting entry",
                "body": "Actors protect their mutable state by serializing all access — only one caller can execute inside the actor at a time, enforced by the compiler, not a lock. Calling an actor method from outside requires await, which suspends the caller until the actor is free. This eliminates data races on actor-isolated state without explicit synchronization primitives.",
                "code": """actor TokenStore {
    private var token: String?

    func setToken(_ newToken: String) {
        token = newToken        // no await needed — already inside actor
    }

    func validToken() -> String? {
        return token            // safe read inside actor
    }
}

// From outside the actor:
let store = TokenStore()
await store.setToken("abc123")          // must await to enter
let t = await store.validToken()        // must await to read""",
                "tip": "A common mistake is thinking actors use a mutex or DispatchQueue internally. They do not — the compiler enforces isolation statically and the runtime schedules re-entry. The interview question 'can two methods run concurrently inside an actor?' is a trap: the answer is no, unless one method suspends with await, at which point another caller can enter."
            },
            {
                "title": "Sendable: safe values crossing actor boundaries",
                "body": "Sendable is a marker protocol indicating a type is safe to share across concurrency domains. The compiler enforces Sendable at actor boundaries: passing a non-Sendable value to an actor method is a compile error in Swift 6 strict concurrency mode. Structs with all-Sendable stored properties are automatically Sendable. @unchecked Sendable opts out of compiler checking — use it only when you guarantee thread safety manually.",
                "code": """// Structs with value-type fields are Sendable automatically
struct WeatherReading: Sendable {
    let temperature: Double
    let timestamp: Date
}

// Class must be manually verified — use @unchecked Sendable with care
final class ImageCache: @unchecked Sendable {
    private let lock = NSLock()
    private var cache: [URL: UIImage] = [:]

    func store(_ image: UIImage, for url: URL) {
        lock.withLock { cache[url] = image }   // manual thread safety
    }
}

actor DataProcessor {
    func process(_ reading: WeatherReading) { /* reading is Sendable — safe */ }
}""",
                "tip": "Interviewers probe Sendable to see if you understand Swift 6's concurrency safety model. @unchecked Sendable is the red flag answer if used without explanation — explain that you are manually guaranteeing thread safety with a lock or other mechanism. The staff-level follow-up: 'What happens with nonisolated(unsafe)?' — it suppresses isolation checking entirely, useful for legacy C interop."
            },
            {
                "title": "async let and TaskGroup: structured parallel work",
                "body": "async let starts a child task immediately and defers awaiting its result to when you need the value — multiple async let bindings run concurrently within the same structured scope. TaskGroup generalizes this to a dynamic number of child tasks. Both are 'structured' because child tasks are cancelled and awaited when the parent scope exits.",
                "code": """// async let — fixed number of parallel tasks
func loadDashboard() async throws -> Dashboard {
    async let user = fetchUser()
    async let feed = fetchFeed()
    async let notifications = fetchNotifications()

    // All three tasks are in flight concurrently; await collects results
    return try await Dashboard(user: user, feed: feed, notifications: notifications)
}

// TaskGroup — dynamic number of parallel tasks
func prefetchImages(urls: [URL]) async -> [URL: UIImage] {
    await withTaskGroup(of: (URL, UIImage)?.self) { group in
        for url in urls {
            group.addTask { try? await (url, downloadImage(url)) }
        }
        var result: [URL: UIImage] = [:]
        for await pair in group { if let p = pair { result[p.0] = p.1 } }
        return result
    }
}""",
                "tip": "The key interview point: async let is not 'background threading' — it is structured concurrency. If the parent function throws before awaiting the async let bindings, the child tasks are automatically cancelled. This automatic cancellation propagation is what makes it 'structured' and is the main advantage over unstructured Task."
            },
        ],
        "try_it": [
            "Rewrite a completion-handler-based URLSession call in your project using async/await. Notice that error handling collapses to a single try/catch instead of multiple guard-let chains inside the completion block.",
            "Create an actor-based cache (e.g., ImageCache) with store and retrieve methods. Write a unit test that calls store and retrieve from concurrent tasks to verify no data races. Run with Thread Sanitizer enabled.",
            "Use async let to parallelize two independent network calls that currently run sequentially. Measure the time difference using ContinuousClock.now before and after.",
            "Enable strict concurrency checking (SWIFT_STRICT_CONCURRENCY = complete) in a build setting and observe which Sendable errors surface. Fix three of them and note the pattern."
        ]
    },
    4: {
        "overview": "GCD remains in production codebases everywhere and understanding it is non-negotiable at the senior level, even as Swift Concurrency takes over new code. Interviewers test whether you can diagnose deadlocks, explain QoS, and articulate the relationship between @MainActor and DispatchQueue.main — a subtle but frequently probed distinction.",
        "concepts": [
            {
                "title": "DispatchQueue serial vs concurrent, async vs sync — and the deadlock trap",
                "body": "A serial queue executes one block at a time in FIFO order. A concurrent queue can execute multiple blocks simultaneously. Dispatching sync onto a queue blocks the calling thread until the block completes. Calling sync on a queue from within that same queue causes an immediate deadlock — the queue is waiting for itself.",
                "code": """let serial = DispatchQueue(label: "com.app.serial")

// Safe: async never blocks the caller
serial.async { print("task 1") }
serial.async { print("task 2") }

// DEADLOCK: sync from within the same serial queue
serial.async {
    serial.sync {   // waits for serial queue to drain — which never happens
        print("never reached")
    }
}

// Safe pattern: sync from a DIFFERENT queue
DispatchQueue.global().async {
    serial.sync { print("safe sync from outside") }
}""",
                "tip": "Deadlock via sync re-entry is the most common GCD interview question. Interviewers often present it as 'what happens here?' with code. The safe rules: never call sync on a queue from within that queue; never call DispatchQueue.main.sync from the main thread (same deadlock, different queue)."
            },
            {
                "title": "QoS classes: which to use when",
                "body": "Quality of Service classes tell the scheduler how urgently work needs CPU time. Using the wrong QoS degrades battery life (using .userInteractive for background work) or creates poor UX (using .background for work the user is visibly waiting for). The system uses QoS to manage thermal state and App Store energy ratings.",
                "code": """// .userInteractive — animations, direct touch response. Highest priority.
DispatchQueue.global(qos: .userInteractive).async { renderFrame() }

// .userInitiated — user tapped a button and is waiting for result (<1 sec)
DispatchQueue.global(qos: .userInitiated).async { loadDocumentPreview() }

// .utility — progress bar visible, user not blocked (seconds to minutes)
DispatchQueue.global(qos: .utility).async { downloadLargeFile() }

// .background — indexing, sync, backup. User unaware. Lowest priority.
DispatchQueue.global(qos: .background).async { rebuildSearchIndex() }""",
                "tip": "Interviewers ask 'what QoS would you use for a network request the user triggered?' The right answer is .userInitiated because the user is actively waiting. A wrong common answer is .default or .background. Staff-level follow-up: 'What happens if you promote a .background task?' — QoS can be elevated by the system if a higher-QoS task depends on it (QoS inversion resolution)."
            },
            {
                "title": "DispatchGroup and barrier writes on concurrent queues",
                "body": "DispatchGroup lets you track a collection of async tasks and get notified when all complete. A barrier block on a concurrent queue waits for all current reads to finish, then executes exclusively, then allows new reads — implementing a safe readers-writer lock pattern without a dedicated class.",
                "code": """// DispatchGroup: wait for multiple async operations
let group = DispatchGroup()
var results: [String] = []
let lock = NSLock()

for url in urls {
    group.enter()
    URLSession.shared.dataTask(with: url) { data, _, _ in
        if let name = parse(data) {
            lock.withLock { results.append(name) }
        }
        group.leave()
    }.resume()
}

group.notify(queue: .main) { updateUI(with: results) }

// Barrier: readers-writer on concurrent queue
let concurrentQueue = DispatchQueue(label: "com.app.rw", attributes: .concurrent)
concurrentQueue.async(flags: .barrier) { sharedDict["key"] = "value" }
concurrentQueue.async { print(sharedDict["key"] ?? "") }  // safe read""",
                "tip": "The barrier pattern is a classic thread-safety interview question. The key insight: .barrier on a serial queue is redundant (serial queues already serialize). Barriers only matter on concurrent queues. Follow-up: 'How does this compare to using an actor?' — an actor is safer and easier, but requires Swift Concurrency. Barriers are the GCD equivalent."
            },
            {
                "title": "Serial queue as a thread-safety lock pattern",
                "body": "A dedicated serial queue is a lightweight alternative to NSLock or os_unfair_lock for protecting mutable state. All reads and writes are dispatched onto the serial queue, guaranteeing they never overlap. The async+sync read pattern returns values synchronously while still executing on the protected queue.",
                "code": """final class SafeCache<Key: Hashable, Value> {
    private var store: [Key: Value] = [:]
    private let queue = DispatchQueue(label: "com.app.safeCache")

    func set(_ value: Value, for key: Key) {
        queue.async { self.store[key] = value }  // fire-and-forget write
    }

    func value(for key: Key) -> Value? {
        queue.sync { store[key] }                // blocking read from caller
    }
}""",
                "tip": "This pattern is widely used in legacy codebases. The interview question is 'why async for writes and sync for reads?' — async writes are safe because callers don't need the result and we want to avoid blocking them. sync reads are necessary to return a value to the caller. The gotcha: sync reads from the queue's own thread deadlock (same re-entry trap as before)."
            },
            {
                "title": "@MainActor vs DispatchQueue.main: same thread, different model",
                "body": "@MainActor is a Swift concurrency actor that uses the main thread as its executor. DispatchQueue.main is a GCD queue backed by the same thread. They are interoperable — @MainActor work runs on DispatchQueue.main's thread — but you should not mix them. Use MainActor.run to hop to the main actor from an async context instead of DispatchQueue.main.async.",
                "code": """// Old pattern — avoid in new async/await code
DispatchQueue.main.async {
    self.label.text = result    // works, but bypasses Swift concurrency
}

// Correct pattern in async context
Task { @MainActor in
    self.label.text = result
}

// Or hop explicitly from non-isolated async code
func updateFromBackground() async {
    let data = await fetchData()
    await MainActor.run {
        label.text = process(data)
    }
}""",
                "tip": "Interviewers ask 'what's the difference between @MainActor and DispatchQueue.main?' The nuanced answer: @MainActor participates in Swift's concurrency model (cooperative scheduling, cancellation propagation, actor reentrancy rules), while DispatchQueue.main is a lower-level primitive that bypasses all of that. Mixing them is legal but creates a maintenance burden and can cause ordering surprises."
            },
        ],
        "try_it": [
            "Create a playground that demonstrates the deadlock: dispatch sync onto a serial queue from within that same serial queue. Then fix it by using async instead and observe the difference.",
            "Implement SafeCache using both the serial-queue pattern and an actor. Write concurrent read/write tests for both using async/await and verify with Thread Sanitizer. Note the difference in code complexity.",
            "Profile a real networking operation in your app with Instruments' Time Profiler. Identify what QoS the URLSession completion handler runs on. Try dispatching UI updates directly from that queue and observe the warning (or crash) from the main thread checker.",
            "Find one instance of DispatchQueue.main.async in your codebase and convert it to await MainActor.run or a @MainActor annotation. Verify the build still passes."
        ]
    },
    5: {
        "overview": "SwiftUI's state and rendering model is the most-probed SwiftUI topic at senior interviews. Interviewers test whether you understand what triggers body re-evaluation, who owns object lifecycle (@StateObject vs @ObservedObject is the #1 mistake), and how View identity affects animation and performance.",
        "concepts": [
            {
                "title": "When body is called: any state change triggers re-evaluation",
                "body": "SwiftUI calls body on a view whenever any @State property changes on that view, or any observed property changes on its @ObservedObject/@StateObject. Importantly, body is called on the view AND all its child views that depend on the same observable. This is why pushing state down to child views and keeping parents lean is a key performance strategy.",
                "code": """struct ParentView: View {
    @State private var counter = 0

    var body: some View {
        VStack {
            // Both children re-render when counter changes,
            // even if CounterDisplay does not use counter.
            CounterDisplay(count: counter)
            ExpensiveStaticView()   // also re-renders unnecessarily
        }
        Button("Increment") { counter += 1 }
    }
}

// Fix: move counter state into CounterDisplay so only it re-renders
struct BetterParentView: View {
    var body: some View {
        VStack {
            CounterDisplay()        // owns its own state
            ExpensiveStaticView()   // never re-renders
        }
    }
}""",
                "tip": "The interview question is 'how do you prevent unnecessary re-renders?' Answers in order of preference: (1) push state down so fewer views observe it, (2) use .equatable() on a view conforming to Equatable, (3) extract into a child view with its own isolated state. Never reach for UIKit as a 'performance fix' before trying these."
            },
            {
                "title": "@State and @Binding: ownership and the init-assignment trap",
                "body": "@State declares that a view owns a piece of value-type state. Passing it to a child as @Binding gives the child a read-write reference to the parent's state without the child owning it. The trap: assigning to a @State property in the view's initializer does not work as expected — the initial value in @State is only used on first render.",
                "code": """struct QuantityPicker: View {
    @Binding var quantity: Int   // parent owns this value

    var body: some View {
        Stepper("Qty: \\(quantity)", value: $quantity, in: 1...99)
    }
}

struct CartItemRow: View {
    @State private var quantity = 1   // this view owns quantity

    var body: some View {
        QuantityPicker(quantity: $quantity)   // pass Binding via $
    }
}

// TRAP: this does NOT update state after first render
struct BrokenView: View {
    @State private var name: String
    init(name: String) { self._name = State(initialValue: name) }  // OK — this form works
    // BUT: self.name = name inside init would silently fail
}""",
                "tip": "The @State init trap is a common senior interview question: 'If I pass a new value to an init that assigns to @State, does the view update?' No — @State is initialized once. To drive a view from external data that changes, use @Binding (child) or @ObservableObject (for complex state). The correct init form if truly needed is State(initialValue:)."
            },
            {
                "title": "@StateObject vs @ObservedObject: object lifecycle ownership",
                "body": "@StateObject creates and owns the object — SwiftUI initializes it once and keeps it alive for the view's lifetime, even across body re-evaluations. @ObservedObject does NOT own the object; the view is handed an existing instance and will observe it, but if the parent re-renders and passes a new instance, the old one is discarded. Using @ObservedObject where you need @StateObject is the #1 SwiftUI bug.",
                "code": """// WRONG: @ObservedObject in a parent-created view
//        Parent re-renders → new ViewModel() created → timer resets every render
struct BrokenTimerView: View {
    @ObservedObject var vm = TimerViewModel()   // re-created on every parent render!
    var body: some View { Text(vm.elapsed) }
}

// CORRECT: @StateObject — created once, survives parent re-renders
struct CorrectTimerView: View {
    @StateObject private var vm = TimerViewModel()  // owned, stable
    var body: some View { Text(vm.elapsed) }
}

// CORRECT: @ObservedObject when the parent passes in an existing instance
struct DetailView: View {
    @ObservedObject var vm: DetailViewModel    // injected, not created here
    var body: some View { Text(vm.title) }
}""",
                "tip": "This is the single most common SwiftUI mistake in senior interviews and production code. If asked 'when would you use @ObservedObject?', the answer is: when the object is created and owned externally (by a parent or coordinator) and injected into the view. Never use @ObservedObject to instantiate a ViewModel inside the view declaration."
            },
            {
                "title": "@EnvironmentObject: convenience vs the runtime crash risk",
                "body": "@EnvironmentObject lets any descendant in a view hierarchy read a shared object without explicit prop-drilling. It is convenient but dangerous: if a view accesses an @EnvironmentObject that was never injected into the hierarchy, the app crashes at runtime with no compile-time warning. Prefer explicit injection for testability; use @EnvironmentObject only for truly global, guaranteed-present state.",
                "code": r"""// Injection at the root
@main struct MyApp: App {
    @StateObject private var session = UserSession()
    var body: some Scene {
        WindowGroup {
            RootView().environmentObject(session)
        }
    }
}

// Any descendant can read it
struct ProfileView: View {
    @EnvironmentObject var session: UserSession    // crashes if not injected
    var body: some View { Text(session.username) }
}

// Safer for testing: use @Environment with a custom key (value-type, default-safe)
struct ProfileView_V2: View {
    @Environment(\.userSession) var session       // default value prevents crash""",
                "tip": "The interview question: 'What's the risk of @EnvironmentObject?' Runtime crash if missing. 'How would you mitigate this in a large codebase?' Two options: (1) use @Environment with a EnvironmentKey that has a default value, (2) inject via initializer so the compiler enforces it. Option 2 is the preferred answer for testability."
            },
            {
                "title": "View identity: structural vs explicit, ForEach performance",
                "body": "SwiftUI uses identity to decide whether to update an existing view or create a new one. Structural identity comes from a view's position in the view tree — two views of the same type in the same position are the same identity. Explicit identity is set with .id(value) or via Identifiable in ForEach. Changing .id() destroys and recreates the view, resetting all @State — useful for forced refresh, but expensive.",
                "code": """// Structural identity — position in tree determines identity
if condition {
    RedView()   // identity A
} else {
    BlueView()  // identity B — different type, different identity
}

// .id() to force recreation (resets @State, animations play from scratch)
TextField("Search", text: $query)
    .id(searchCategory)   // new category → new TextField → state reset

// ForEach requires stable IDs — unstable IDs cause unnecessary recreation
ForEach(items) { item in   // item.id must be stable, unique
    ItemRow(item: item)
}
// AVOID: ForEach(items, id: \\.self) on mutable structs — every mutation changes identity""",
                "tip": "The .id() trick for force-refreshing a view (e.g., resetting a form) appears in many interviews as a 'how would you clear this view's state?' question. The correct answer is .id(someChangingValue). The follow-up: 'What's the performance cost?' — the entire view subtree is destroyed and recreated, including animations from scratch. Use sparingly."
            },
        ],
        "try_it": [
            "Add Self._printChanges() as the first line in a SwiftUI view's body. Navigate through your app and observe in the console which property changes are triggering re-renders. Find one view that re-renders more than expected and refactor to reduce it.",
            "Create a view that mistakenly uses @ObservedObject to instantiate a ViewModel. Add a Timer in the ViewModel's init that prints a message. Navigate to a parent view that re-renders and watch the timer reset. Then switch to @StateObject and confirm it fires once.",
            "Build a form with @State fields and a Reset button that uses the .id() trick to reset all fields simultaneously. Observe in the debugger that SwiftUI destroys and recreates the entire form subtree.",
            "Replace one @EnvironmentObject usage with a custom EnvironmentKey that has a meaningful default value. Write a unit test that creates the view without any environment injection and confirm it does not crash."
        ]
    },
    6: {
        "overview": "SwiftUI/UIKit interop is a practical daily concern for any team migrating an existing UIKit app or integrating components that have no SwiftUI equivalent. Senior interviewers test whether you know the correct lifecycle methods, can implement the Coordinator pattern correctly, and understand the sizing challenges of UIHostingController.",
        "concepts": [
            {
                "title": "UIViewRepresentable: makeUIView, updateUIView, and idempotency",
                "body": "UIViewRepresentable bridges a UIKit view into SwiftUI. makeUIView is called once to create the view. updateUIView is called every time SwiftUI's state changes and must be idempotent — safe to call multiple times with the same data. A common mistake is doing expensive setup in updateUIView that should be in makeUIView.",
                "code": """struct MapPinView: UIViewRepresentable {
    let coordinate: CLLocationCoordinate2D

    func makeUIView(context: Context) -> MKMapView {
        let map = MKMapView()
        map.mapType = .standard      // one-time setup
        return map
    }

    func updateUIView(_ mapView: MKMapView, context: Context) {
        // Called on every SwiftUI state change — must be idempotent
        let region = MKCoordinateRegion(
            center: coordinate,
            latitudinalMeters: 500,
            longitudinalMeters: 500
        )
        mapView.setRegion(region, animated: true)
    }
}""",
                "tip": "The idempotency requirement is the most common UIViewRepresentable interview mistake. Candidates write code in updateUIView that adds subviews or registers observers on every call, creating duplicates. The rule: makeUIView for one-time setup; updateUIView only for data sync. Ask yourself: 'Is it safe to call this ten times in a row with the same data?' If not, it's in the wrong method."
            },
            {
                "title": "Coordinator pattern: UIKit delegates need a coordinator",
                "body": "UIKit delegates (UITextFieldDelegate, MKMapViewDelegate, etc.) are class-based reference types that must be retained. SwiftUI views are structs and cannot act as delegates. The Coordinator is a class you create in makeCoordinator() — SwiftUI retains it for the lifetime of the representable. The context parameter in makeUIView gives you access to the coordinator.",
                "code": """struct SearchField: UIViewRepresentable {
    @Binding var text: String

    func makeCoordinator() -> Coordinator {
        Coordinator(text: $text)      // SwiftUI retains this
    }

    func makeUIView(context: Context) -> UITextField {
        let field = UITextField()
        field.delegate = context.coordinator  // coordinator is the delegate
        return field
    }

    func updateUIView(_ field: UITextField, context: Context) {
        field.text = text
    }

    class Coordinator: NSObject, UITextFieldDelegate {
        @Binding var text: String
        init(text: Binding<String>) { _text = text }

        func textFieldDidChangeSelection(_ textField: UITextField) {
            text = textField.text ?? ""
        }
    }
}""",
                "tip": "The interview question is 'why can't the SwiftUI view struct itself be the delegate?' Because structs have no stable identity — SwiftUI recreates them constantly. UIKit retains delegates weakly or strongly, and a pointer to a reconstructed struct is dangling. The coordinator's class-based stable identity is the key."
            },
            {
                "title": "UIViewControllerRepresentable: lifecycle and dismantleUIViewController",
                "body": "UIViewControllerRepresentable follows the same pattern as UIViewRepresentable but wraps a full UIViewController. Critically, dismantleUIViewController is called when SwiftUI removes the representable from the hierarchy — use it to deregister observers, stop timers, or cancel subscriptions that the view controller started.",
                "code": """struct DocumentPickerView: UIViewControllerRepresentable {
    var onPick: (URL) -> Void

    func makeUIViewController(context: Context) -> UIDocumentPickerViewController {
        let picker = UIDocumentPickerViewController(forOpeningContentTypes: [.pdf])
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ vc: UIDocumentPickerViewController, context: Context) {
        // Usually empty for modal controllers
    }

    static func dismantleUIViewController(_ vc: UIDocumentPickerViewController,
                                          coordinator: Coordinator) {
        // Cancel any subscriptions or observers started in makeUIViewController
        coordinator.cleanup()
    }

    func makeCoordinator() -> Coordinator { Coordinator(onPick: onPick) }
}""",
                "tip": "dismantleUIViewController is frequently forgotten and leads to leaks. The interview probe: 'What happens if your UIViewControllerRepresentable starts a NotificationCenter observer?' Without dismantleUIViewController cleaning it up, the observer fires after the view is gone. This is a code review red flag interviewers look for."
            },
            {
                "title": "UIHostingController: embedding SwiftUI in UIKit and sizing challenges",
                "body": "UIHostingController wraps a SwiftUI view tree and presents it as a UIViewController, letting you drop SwiftUI into an existing UIKit hierarchy. The main challenge is sizing: UIHostingController does not automatically communicate intrinsic content size back to UIKit, requiring either Auto Layout constraints or manual sizeThatFits calls.",
                "code": """// Embedding a SwiftUI badge view in a UITableViewCell
class ProfileCell: UITableViewCell {
    private var hostingController: UIHostingController<BadgeView>?

    func configure(with badge: Badge) {
        let badgeView = BadgeView(badge: badge)
        let host = UIHostingController(rootView: badgeView)
        host.view.translatesAutoresizingMaskIntoConstraints = false
        host.view.backgroundColor = .clear

        contentView.addSubview(host.view)
        NSLayoutConstraint.activate([
            host.view.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 8),
            host.view.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
        ])
        // Must call _disableSafeArea on iOS <16 or use .fixedSize() on the SwiftUI view
        hostingController = host
    }
}""",
                "tip": "The sizing issue is the most common UIHostingController interview concern. Before iOS 16, you often needed host.view.invalidateIntrinsicContentSize() or manual sizeThatFits:. iOS 16+ added sizingOptions. The other pitfall: the UIHostingController must be added as a child view controller (addChild/didMove) or it will not receive UIKit lifecycle events."
            },
            {
                "title": "Navigation migration: NavigationStack path model vs UINavigationController",
                "body": "Migrating from UINavigationController to NavigationStack requires adopting the path-based navigation model. The NavigationPath (or typed array) becomes the single source of truth for the stack, enabling deep link navigation and programmatic stack manipulation that was cumbersome with UINavigationController push/pop calls.",
                "code": """// Modern NavigationStack with typed path
@Observable
class NavigationModel {
    var path: [AppRoute] = []

    func push(_ route: AppRoute) { path.append(route) }
    func popToRoot() { path.removeAll() }
    func navigate(to route: AppRoute) { path = [route] }
}

enum AppRoute: Hashable {
    case profile(userID: UUID)
    case settings
    case articleDetail(id: String)
}

struct RootView: View {
    @State private var nav = NavigationModel()

    var body: some View {
        NavigationStack(path: $nav.path) {
            HomeView()
                .navigationDestination(for: AppRoute.self) { route in
                    switch route {
                    case .profile(let id): ProfileView(userID: id)
                    case .settings: SettingsView()
                    case .articleDetail(let id): ArticleView(id: id)
                    }
                }
        }
        .environment(nav)
    }
}""",
                "tip": "The interview question: 'How would you handle deep links with NavigationStack?' The answer is manipulating the path array directly — replace it with the desired route sequence and SwiftUI animates to that state. With UINavigationController you had to push/pop imperatively. The path model is declarative and easily serializable for state restoration."
            },
        ],
        "try_it": [
            "Wrap MKMapView in UIViewRepresentable with a Coordinator that handles MKMapViewDelegate. Intentionally do expensive setup in updateUIView, observe the repeated work in Instruments, then move it to makeUIView.",
            "Add a UIHostingController hosting a SwiftUI stats card into an existing UITableViewCell or UICollectionViewCell. Correctly add it as a child view controller and verify lifecycle methods fire by printing in SwiftUI onAppear/onDisappear.",
            "Build a NavigationStack-based navigation model for an app with 3 routes. Implement a deep link handler that sets the path directly. Test that popping and pushing programmatically works without the back stack getting corrupted.",
            "Find a UIViewRepresentable in your codebase (or write one) that is missing dismantleUIViewController/dismantleUIView. Add cleanup logic and verify with the Memory Graph Debugger that the UIKit component is released when the SwiftUI view leaves the hierarchy."
        ]
    },
    7: {
        "overview": "Architecture and modularization are the highest-signal topics at the staff level because they reflect how you structure an entire team's work, not just a single feature. Interviewers probe whether you have opinions about tradeoffs between patterns, can articulate failure modes, and have shipped code at the scale where modularization actually matters.",
        "concepts": [
            {
                "title": "MVVM with ObservableObject: clear boundaries and the massive ViewModel failure mode",
                "body": "MVVM works well in SwiftUI when ViewModels are focused: one per screen, responsible for state transformation and user intent handling, not for networking or persistence directly. The failure mode is the massive ViewModel that owns network calls, Core Data contexts, and business logic simultaneously — it becomes untestable and nearly as bad as Massive View Controller.",
                "code": """// Focused ViewModel — depends on protocol, testable
@MainActor
@Observable
final class ArticleListViewModel {
    private let repository: ArticleRepository   // injected protocol

    var articles: [Article] = []
    var isLoading = false
    var errorMessage: String?

    init(repository: ArticleRepository) {
        self.repository = repository
    }

    func loadArticles() async {
        isLoading = true
        defer { isLoading = false }
        do {
            articles = try await repository.fetchAll()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

protocol ArticleRepository {
    func fetchAll() async throws -> [Article]
}""",
                "tip": "The tell-tale sign of a massive ViewModel in code review: it imports both Foundation and CoreData and has 500+ lines. The fix is extracting a Repository (data layer) and UseCase (business logic) layer, leaving the ViewModel as a pure state transformer. Interviewers who ask 'how do you keep ViewModels lean?' want to hear about layering, not just 'break it into smaller ViewModels.'"
            },
            {
                "title": "Unidirectional data flow (UDF): Action→State→View cycle",
                "body": "Unidirectional data flow enforces that state changes follow a single path: user actions are dispatched as typed Actions, a reducer transforms the current State into a new State, and the View renders the State. This makes every state transition explicit, reproducible, and testable in isolation. The Composable Architecture (TCA) is the dominant Swift implementation.",
                "code": """// Minimal UDF sketch (illustrative, not full TCA)
struct FeedState: Equatable {
    var articles: [Article] = []
    var isLoading = false
}

enum FeedAction {
    case loadArticles
    case articlesLoaded([Article])
    case loadFailed(Error)
}

func feedReducer(state: inout FeedState, action: FeedAction) {
    switch action {
    case .loadArticles:
        state.isLoading = true
    case .articlesLoaded(let articles):
        state.articles = articles
        state.isLoading = false
    case .loadFailed:
        state.isLoading = false
    }
}
// Test: call feedReducer with .articlesLoaded, assert state.articles is set""",
                "tip": "Staff interviewers ask 'what does UDF give you that MVVM doesn't?' The answer: every state transition is an explicit, serializable value (the Action) — you can log, replay, and time-travel debug them. The tradeoff is boilerplate. Be ready to discuss when UDF overhead is not worth it (simple screens) vs. when it shines (complex multi-step flows with many actors)."
            },
            {
                "title": "Protocol-based dependency injection: live vs mock, avoiding singletons",
                "body": "Defining service dependencies as protocols lets you swap live implementations with test doubles without changing the consuming type. Constructor injection makes dependencies explicit and prevents hidden coupling. Singletons are the enemy of testability — a type that calls NetworkManager.shared internally is untestable in isolation.",
                "code": """protocol AnalyticsService: Sendable {
    func track(event: AnalyticsEvent) async
}

struct FirebaseAnalyticsService: AnalyticsService {
    func track(event: AnalyticsEvent) async {
        // Real Firebase call
    }
}

struct MockAnalyticsService: AnalyticsService {
    var trackedEvents: [AnalyticsEvent] = []
    func track(event: AnalyticsEvent) async {
        trackedEvents.append(event)    // record for assertion
    }
}

// Injected at construction time — testable, mockable
final class CheckoutViewModel {
    private let analytics: AnalyticsService
    init(analytics: AnalyticsService = FirebaseAnalyticsService()) {
        self.analytics = analytics
    }
}""",
                "tip": "Interviewers probe: 'How do you handle a type that needs 5 service dependencies?' The answer leads to a discussion of DI containers or factory patterns. Be ready to discuss the tradeoff between explicit constructor injection (transparent, compile-time checked) and a DI container (less boilerplate but runtime-resolved). For Swift, explicit injection is usually preferred for its type safety."
            },
            {
                "title": "Swift Package Manager modularization: feature/domain/shared split",
                "body": "Splitting an app into SPM local packages enforces architectural boundaries at the compiler level — a feature module literally cannot import another feature module's internal types. The standard layering is: Shared (design system, utilities) → Domain (business models, protocols) → Feature (screen-level modules that depend on Domain). Build time improves because changed modules are recompiled in isolation.",
                "code": """// Package.swift structure (illustrative)
// Packages/
//   Shared/          — UIComponents, Extensions, Analytics protocols
//   Domain/          — User, Article, Order models + Repository protocols
//   NetworkKit/      — URLSession wrapper, implements Domain protocols
//   FeedFeature/     — SwiftUI screens for the feed
//   ProfileFeature/  — SwiftUI screens for profile

// FeedFeature/Package.swift
.target(
    name: "FeedFeature",
    dependencies: [
        .product(name: "Domain", package: "Domain"),
        .product(name: "Shared", package: "Shared"),
        // NOT allowed to import ProfileFeature — enforced by compiler
    ]
)""",
                "tip": "The staff interview question: 'How do two feature modules communicate without importing each other?' The answer: via abstractions in the Domain layer — protocols or published value types. A direct import between feature modules signals a missing abstraction. This is how Conway's Law applies: module topology should mirror team topology."
            },
            {
                "title": "Feature flags: runtime toggles, targeted rollouts, and flag debt",
                "body": "Feature flags decouple deployment from release, enabling dark launches, A/B tests, and kill switches. They should be resolved at the boundary (ViewModel or coordinator), not scattered throughout view code. Flag debt — flags that are never cleaned up — is a real maintenance problem: every active flag multiplies code paths and test cases.",
                "code": """protocol FeatureFlagService {
    func isEnabled(_ flag: FeatureFlag) -> Bool
}

enum FeatureFlag: String {
    case newCheckoutFlow = "new_checkout_flow"
    case aiSuggestions   = "ai_suggestions"
}

@MainActor
final class AppCoordinator {
    private let flags: FeatureFlagService

    init(flags: FeatureFlagService) { self.flags = flags }

    func checkoutView() -> some View {
        if flags.isEnabled(.newCheckoutFlow) {
            NewCheckoutView()
        } else {
            LegacyCheckoutView()
        }
    }
}

// Cleanup rule: file a ticket to remove a flag 2 sprints after 100% rollout""",
                "tip": "Flag debt is a real interview topic at staff level. A strong answer includes a governance policy: flags have an owner, a removal date filed as a ticket at creation time, and are not merged without a plan to clean them up. Interviewers who manage large codebases will appreciate this operational thinking."
            },
        ],
        "try_it": [
            "Draw the dependency graph of your current app's main screen ViewModel. Count how many concrete types it depends on directly. Refactor the heaviest concrete dependency to a protocol and inject a mock in a new unit test.",
            "Create a local SPM package for your app's shared UI components. Move one view and verify the main app target still builds. Observe that the shared package's internal types are not visible in the main target unless explicitly exported.",
            "Add a simple in-memory FeatureFlagService to your app with two flags. Gate a UI change behind one flag. Write a test that exercises both the enabled and disabled code paths by injecting a mock flag service.",
            "Count the number of singletons (ClassName.shared) called from ViewModels in your codebase. Pick one and refactor it to constructor injection with a protocol. Note whether tests become easier to write afterward."
        ]
    },
    8: {
        "overview": "Persistence is probed at the senior level through the lens of correctness, not just API knowledge. Interviewers want to know if you understand Core Data's threading model (the source of the most common crashes), how SwiftData differs, and whether you can design a migration strategy that does not corrupt user data.",
        "concepts": [
            {
                "title": "Core Data stack: NSPersistentContainer, main vs background MOC",
                "body": "NSPersistentContainer is the modern Core Data entry point, providing viewContext (main thread) and newBackgroundContext() for background work. The cardinal rule: never pass an NSManagedObject across contexts. Objects fetched on the background context must be converted to ObjectIDs and re-fetched on the main context before touching the UI.",
                "code": """let container = NSPersistentContainer(name: "Model")
container.loadPersistentStores { _, error in
    if let error { fatalError("Core Data load failed: \\(error)") }
}

// Background save — performBackgroundTask gives a short-lived context
container.performBackgroundTask { context in
    let article = Article(context: context)
    article.title = "Swift 6 Deep Dive"
    article.id = UUID()
    try? context.save()
}

// Main context reads — always on main thread
let fetchRequest = Article.fetchRequest()
fetchRequest.sortDescriptors = [NSSortDescriptor(key: "createdAt", ascending: false)]
let articles = try? container.viewContext.fetch(fetchRequest)""",
                "tip": "The threading crash is the #1 Core Data interview topic: 'What error does Core Data throw when you access an object on the wrong thread?' Answer: it may not throw — it may just corrupt silently or crash with EXC_BAD_ACCESS. This is why the threading contract matters. Follow-up: 'How do you safely pass data from a background context to the main context?' Answer: use objectID and fetch on viewContext."
            },
            {
                "title": "NSFetchRequest: predicates, batch sizes, and faulting",
                "body": "NSFetchRequest is Core Data's query mechanism. Setting fetchBatchSize causes Core Data to load objects in chunks rather than all at once, dramatically reducing memory usage for large result sets. Faulting is the mechanism by which relationship objects are placeholders until accessed — a property access on a fault fires a round-trip to the persistent store.",
                "code": """let request: NSFetchRequest<Article> = Article.fetchRequest()

// Predicate — uses NSExpression, not Swift operators
request.predicate = NSPredicate(format: "isBookmarked == YES AND author == %@", authorName)

// Sort descriptor
request.sortDescriptors = [NSSortDescriptor(keyPath: \\Article.createdAt, ascending: false)]

// Batch size — Core Data loads 20 at a time; saves memory for 10,000+ rows
request.fetchBatchSize = 20

// Fetch only what you need — avoids firing faults on relationships
request.relationshipKeyPathsForPrefetching = ["tags"]  // pre-fetch tags relationship

let results = try context.fetch(request)""",
                "tip": "fetchBatchSize is underused and the correct answer to 'how do you efficiently display 10,000 Core Data objects in a list?' Not setting it means all 10,000 objects are materialized in memory. The follow-up: 'What is a Core Data fault?' A placeholder object whose properties are loaded on first access. Firing many faults in a loop causes N+1 query problems — use relationshipKeyPathsForPrefetching to batch-load relationships."
            },
            {
                "title": "Core Data concurrency: background import, automaticallyMergesChangesFromParent",
                "body": "Setting automaticallyMergesChangesFromParent = true on viewContext causes it to automatically pick up changes saved by background contexts, triggering NSFetchedResultsController updates. Without this, background saves are invisible to the UI. Merge policies resolve conflicts when both contexts modify the same object.",
                "code": """// Set up viewContext to auto-merge background saves
container.viewContext.automaticallyMergesChangesFromParent = true
container.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy

// Background bulk import
container.performBackgroundTask { bgContext in
    bgContext.mergePolicy = NSMergeByPropertyStoreTrumpMergePolicy

    for item in serverData {
        let entity = ManagedItem(context: bgContext)
        entity.id = item.id
        entity.name = item.name
    }

    do {
        try bgContext.save()  // triggers merge into viewContext automatically
    } catch {
        bgContext.rollback()
        print("Import failed: \\(error)")
    }
}""",
                "tip": "automaticallyMergesChangesFromParent is the most commonly missing setup step in Core Data implementations. Without it, your UI never updates after background saves. The merge policy question is also common: NSMergeByPropertyObjectTrumpMergePolicy means 'in-memory wins over store', which is right for user edits; NSMergeByPropertyStoreTrumpMergePolicy means 'store wins', which is right for server syncs."
            },
            {
                "title": "SwiftData: @Model, ModelContainer, and @Query in SwiftUI",
                "body": "SwiftData is Apple's modern persistence framework built on Core Data internals. @Model macro transforms a class into a persistent model. ModelContainer is the equivalent of NSPersistentContainer. @Query in SwiftUI replaces NSFetchedResultsController, directly driving list updates when the underlying data changes.",
                "code": """import SwiftData

@Model
final class Article {
    var id: UUID
    var title: String
    var isBookmarked: Bool
    var createdAt: Date

    init(id: UUID = UUID(), title: String, isBookmarked: Bool = false) {
        self.id = id
        self.title = title
        self.isBookmarked = isBookmarked
        self.createdAt = Date()
    }
}

// SwiftUI view with live query
struct ArticleListView: View {
    @Query(sort: \\Article.createdAt, order: .reverse)
    private var articles: [Article]

    @Environment(\\.modelContext) private var context

    var body: some View {
        List(articles) { article in ArticleRow(article: article) }
            .toolbar {
                Button("Add") {
                    context.insert(Article(title: "New Article"))
                }
            }
    }
}""",
                "tip": "SwiftData interviews often include: 'What's the relationship between SwiftData and Core Data?' SwiftData is backed by Core Data's store — they can share the same SQLite file and even operate on the same data. The key limitation as of iOS 17-18: SwiftData has less control over background contexts and complex migrations than Core Data. For greenfield apps, SwiftData is preferred; for existing Core Data apps, the interop path exists but is careful work."
            },
            {
                "title": "Migration: lightweight vs custom mapping model, and migration CI tests",
                "body": "Lightweight migration handles additive changes (new attributes with defaults, new entities, renamed attributes flagged with renamingIdentifier). Custom mapping models handle complex transformations — splitting entities, computing derived values, or changing attribute types. Both require a model version history. A migration CI test catches broken migrations before they corrupt user data in production.",
                "code": """// In Core Data model editor: add a new model version, set as current
// Lightweight migration (additive — no mapping model needed):
let options = [
    NSMigratePersistentStoresAutomaticallyOption: true,
    NSInferMappingModelAutomaticallyOption: true
]
try coordinator.addPersistentStore(
    ofType: NSSQLiteStoreType,
    configurationName: nil,
    at: storeURL,
    options: options
)

// Migration test — run in CI against a real copy of an old store
func test_migration_v1ToV2_preservesArticleCount() throws {
    let oldStoreURL = Bundle(for: Self.self).url(forResource: "v1_fixture", withExtension: "sqlite")!
    // Load v1 store, run migration, assert v2 entity counts match expected
    let container = makeMigratedContainer(from: oldStoreURL)
    let count = try container.viewContext.count(for: Article.fetchRequest())
    XCTAssertEqual(count, 42)   // known fixture count
}""",
                "tip": "The staff-level migration question: 'How do you test that a Core Data migration doesn't corrupt existing user data?' The answer is a migration test: ship a SQLite fixture (a copy of a real or synthetic old-version store) in the test bundle, run migration against it, and assert entity counts and spot-check field values. Without this test, a broken migration reaches users and corrupts their data permanently."
            },
        ],
        "try_it": [
            "Enable Core Data concurrency debugging by adding -com.apple.CoreData.ConcurrencyDebug 1 to your scheme's launch arguments. Run your app and see if any threading violations are reported.",
            "Write a background import of 1,000 objects using performBackgroundTask. Time it with ContinuousClock. Then observe that the UI list updates automatically thanks to automaticallyMergesChangesFromParent.",
            "Create a SwiftData model with @Query, build a simple CRUD interface, and then add a new attribute to the @Model class. Observe whether migration is handled automatically and what happens to existing records.",
            "Create a v1 Core Data fixture (SQLite file), add a new attribute in a v2 model version, and write a migration test that loads the v1 fixture and verifies the migrated v2 data is correct."
        ]
    },
    9: {
        "overview": "Networking is a daily concern and interviewers test whether you design it correctly, not just whether you can call URLSession. The key topics are the distinction between transport errors and HTTP errors, designing a testable API client, and correctly handling cancellation — which async/await makes much cleaner than the callback era.",
        "concepts": [
            {
                "title": "URLSession async/await: transport errors vs HTTP errors",
                "body": "URLSession.data(for:) throws only for transport-layer errors (no connectivity, SSL failure, timeout). It does NOT throw for HTTP error status codes like 404 or 500 — those come back as a successful result with an HTTPURLResponse. Failing to check the HTTP status code means your app silently treats server errors as successes.",
                "code": """func fetchArticle(id: String) async throws -> Article {
    let url = URL(string: "https://api.example.com/articles/\\(id)")!
    let (data, response) = try await URLSession.shared.data(from: url)
    // transport error throws above; HTTP errors do NOT throw

    guard let http = response as? HTTPURLResponse else {
        throw APIError.invalidResponse
    }
    guard (200...299).contains(http.statusCode) else {
        throw APIError.httpError(statusCode: http.statusCode)
    }

    return try JSONDecoder().decode(Article.self, from: data)
}

enum APIError: Error {
    case invalidResponse
    case httpError(statusCode: Int)
}""",
                "tip": "This transport-vs-HTTP distinction is the #1 networking interview mistake. Candidates write 'let (data, _) = try await ...' dropping the response, then wonder why the app shows success on a 503. Always check the status code. Follow-up: 'How would you handle retries on 503?' — exponential backoff with jitter, max retry count, and respect for Retry-After headers."
            },
            {
                "title": "Codable: CodingKeys, dateDecodingStrategy, and custom init for mixed types",
                "body": "Codable's automatic synthesis is convenient but breaks for renamed keys, non-ISO dates, or server APIs that return a field as either a String or Int. CodingKeys enum handles renames. JSONDecoder.dateDecodingStrategy handles date formats. A custom init(from:) handles mixed-type fields that automatic synthesis cannot express.",
                "code": """struct Event: Codable {
    let eventId: Int
    let title: String
    let startDate: Date
    let metadata: Metadata

    enum CodingKeys: String, CodingKey {
        case eventId = "event_id"   // snake_case → camelCase
        case title
        case startDate = "start_date"
        case metadata
    }
}

struct Metadata: Codable {
    let value: String

    // Server returns "value" as either String or Int
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        if let s = try? container.decode(String.self, forKey: .value) {
            value = s
        } else if let i = try? container.decode(Int.self, forKey: .value) {
            value = String(i)
        } else {
            throw DecodingError.typeMismatch(String.self, .init(codingPath: [], debugDescription: "Expected String or Int"))
        }
    }
}

let decoder = JSONDecoder()
decoder.dateDecodingStrategy = .iso8601""",
                "tip": "The custom init(from:) for mixed types is a real-world problem from inconsistent APIs and appears in senior interviews as a 'how would you handle a field that can be a String or a number?' question. The wrong answer is to make the property Any — that defeats type safety. The right answer is a custom decode that tries each type in order."
            },
            {
                "title": "Protocol-based API client design: endpoint enum and injected URLSession",
                "body": "A well-designed API client separates endpoint definition (what to request) from execution (how to request it). An endpoint enum with associated values encodes the path, method, and body per request. Injecting URLSession as a protocol makes the client testable with a mock session that returns fixture data without hitting the network.",
                "code": """protocol HTTPClient {
    func send<T: Decodable>(_ endpoint: Endpoint) async throws -> T
}

enum Endpoint {
    case getArticle(id: String)
    case createComment(articleId: String, body: CommentRequest)

    var urlRequest: URLRequest {
        switch self {
        case .getArticle(let id):
            return URLRequest(url: URL(string: "https://api.example.com/articles/\\(id)")!)
        case .createComment(let articleId, let body):
            var req = URLRequest(url: URL(string: "https://api.example.com/articles/\\(articleId)/comments")!)
            req.httpMethod = "POST"
            req.httpBody = try? JSONEncoder().encode(body)
            return req
        }
    }
}

struct LiveHTTPClient: HTTPClient {
    private let session: URLSession
    init(session: URLSession = .shared) { self.session = session }

    func send<T: Decodable>(_ endpoint: Endpoint) async throws -> T {
        let (data, response) = try await session.data(for: endpoint.urlRequest)
        guard (response as? HTTPURLResponse).map({ (200...299).contains($0.statusCode) }) == true else {
            throw APIError.httpError
        }
        return try JSONDecoder().decode(T.self, from: data)
    }
}""",
                "tip": "This design pattern (endpoint enum + injectable session) is considered best practice and interviewers use it to distinguish candidates who have designed API clients from those who have only used them. The follow-up: 'How do you test this without hitting the network?' Answer: URLProtocol subclass or a protocol-based URLSession wrapper that returns pre-built responses."
            },
            {
                "title": "Cancellation: .task modifier auto-cancel and manual Task.cancel()",
                "body": "The SwiftUI .task modifier automatically starts an async task when the view appears and cancels it when the view disappears — this is the correct way to bind async work to view lifetime. For tasks started manually (in a ViewModel), you must cancel them explicitly by storing the Task handle and calling .cancel() on deinit or on a new request.",
                "code": """// .task modifier — auto-cancelled when view disappears
struct ArticleView: View {
    @State private var article: Article?
    let articleId: String

    var body: some View {
        ArticleContent(article: article)
            .task {
                // Cancelled automatically if view disappears before completion
                article = try? await fetchArticle(id: articleId)
            }
    }
}

// Manual cancellation in ViewModel
@MainActor
final class SearchViewModel {
    private var searchTask: Task<Void, Never>?

    func search(query: String) {
        searchTask?.cancel()   // cancel previous search before starting new one
        searchTask = Task {
            guard !Task.isCancelled else { return }
            let results = try? await searchService.search(query: query)
            if !Task.isCancelled { self.results = results ?? [] }
        }
    }
}""",
                "tip": "The .task modifier is the correct answer to 'how do you avoid a race condition where a dismissed view tries to update its @State?' Auto-cancellation handles it. For ViewModel tasks, the pattern of cancelling the previous Task before starting a new one (for search-as-you-type) is a common interview question. Check Task.isCancelled after each await to avoid processing stale results."
            },
            {
                "title": "Caching: URLCache, ETag conditional requests, and cache-then-network",
                "body": "URLCache caches responses automatically if the server sets Cache-Control headers. For more control, ETag/If-None-Match conditional requests let the client ask 'has this changed?' and get a 304 Not Modified (no body) rather than a full response, saving bandwidth. The cache-then-network pattern shows cached content immediately, then updates when fresh data arrives.",
                "code": """// Cache-then-network pattern
func loadFeed() async {
    // 1. Show cached data immediately (from URLCache or local DB)
    if let cached = await localCache.articles() {
        self.articles = cached
    }

    // 2. Fetch fresh data in parallel
    do {
        var request = URLRequest(url: feedURL)
        // Send stored ETag — server returns 304 if unchanged
        if let etag = UserDefaults.standard.string(forKey: "feedETag") {
            request.setValue(etag, forHTTPHeaderField: "If-None-Match")
        }

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else { return }

        if http.statusCode == 304 { return }  // not modified — keep showing cache

        if let newEtag = http.value(forHTTPHeaderField: "ETag") {
            UserDefaults.standard.set(newEtag, forKey: "feedETag")
        }
        articles = try JSONDecoder().decode([Article].self, from: data)
    } catch { /* handle */ }
}""",
                "tip": "The cache-then-network pattern is the expected answer to 'how do you make your app work well on slow connections?' It shows a UX-aware candidate. ETags are a signal that you understand HTTP caching at the protocol level, not just URLCache. A strong follow-up answer: 'I'd also use a write-through local database (Core Data/SwiftData) as the cache, so the pattern degrades gracefully offline.'"
            },
        ],
        "try_it": [
            "Add -com.apple.URLSession.log to your scheme arguments and run a network call. Observe the full HTTP request and response in the console, including status codes. Find one call that does not check the HTTP status code and fix it.",
            "Write a MockURLProtocol that intercepts URLSession requests and returns fixture JSON from a file. Register it with URLSessionConfiguration and use it to test your API client without network access.",
            "Implement search-as-you-type with a 300ms debounce. Cancel the previous search Task before starting a new one. Test that rapid input does not result in out-of-order result sets by logging task start/cancel events.",
            "Inspect the Cache-Control headers returned by an API your app uses (using Charles Proxy or URLSession logging). If caching is not configured, implement a manual ETag cache for the most-frequently-called endpoint."
        ]
    },
    10: {
        "overview": "Performance and profiling distinguish engineers who fix bugs from engineers who prevent them. Senior interviewers ask about Instruments because it reveals whether you have debugged real performance problems, not just read about them. The 16ms main thread rule and memory pressure handling are the most frequently cited production failure modes.",
        "concepts": [
            {
                "title": "Time Profiler: flame graph and the 'Invert Call Tree + Hide System Libraries' filter",
                "body": "Instruments' Time Profiler samples the call stack at 1ms intervals. The default flame graph shows the full call tree — mostly system framework calls that you cannot control. Enabling 'Invert Call Tree' shows the leaf functions (actual work) at the top, and 'Hide System Libraries' removes Apple framework frames, leaving only your code. This combination reveals the real bottleneck in seconds.",
                "code": """// Before optimization — all work on main thread:
func collectionView(_ cv: UICollectionView,
                    cellForItemAt indexPath: IndexPath) -> UICollectionViewCell {
    let cell = cv.dequeueReusableCell(withReuseIdentifier: "Cell", for: indexPath)
    // These run synchronously on the main thread — Time Profiler will show them
    let image = loadImage(from: items[indexPath.item].thumbnailURL)  // disk I/O!
    let processed = applyFilters(image)                               // CPU-heavy!
    cell.imageView.image = processed
    return cell
}

// After: move work off main thread
func collectionView(_ cv: UICollectionView,
                    cellForItemAt indexPath: IndexPath) -> UICollectionViewCell {
    let cell = cv.dequeueReusableCell(withReuseIdentifier: "Cell", for: indexPath) as! ImageCell
    let url = items[indexPath.item].thumbnailURL
    cell.configure(with: url)   // async load + cache inside the cell
    return cell
}""",
                "tip": "When an interviewer asks 'how do you find a performance problem?', the answer is Time Profiler with Invert Call Tree + Hide System Libraries. This is a specific, demonstrable skill. The wrong answer is 'I add print statements and time things manually.' Knowing the filter combination shows you have used the tool on a real problem."
            },
            {
                "title": "Allocations: heapshots and generation diff for finding leaks",
                "body": "The Allocations instrument tracks every heap allocation. The generation diff technique: take a heapshot before a user action, perform the action, take another heapshot, then view the diff to see exactly what objects were allocated and not yet released. Repeating this across multiple action cycles reveals objects that accumulate rather than being freed.",
                "code": """// Pattern that causes accumulating allocations (leak-like):
class ViewController: UIViewController {
    var observers: [NSObjectProtocol] = []

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        // Bug: adds a new observer every time the view appears
        let obs = NotificationCenter.default.addObserver(
            forName: .dataUpdated, object: nil, queue: .main
        ) { [weak self] _ in self?.reload() }
        observers.append(obs)
        // Fix: check if observers is empty before registering
    }

    deinit {
        observers.forEach { NotificationCenter.default.removeObserver($0) }
    }
}""",
                "tip": "The generation diff technique is the tool-specific answer interviewers want when they ask 'how do you find a memory leak that doesn't show up as a retain cycle?' Not all leaks are retain cycles — repeated observer registration, growing caches, or appending to arrays without bounds are 'accumulation leaks' that only show up in heapshot diffs. Knowing the technique by name impresses senior-level interviewers."
            },
            {
                "title": "Hangs: Thread Performance Checker, MetricKit, and the 16ms rule",
                "body": "A hang occurs when the main thread is blocked for more than ~16ms (one frame at 60 fps). The Thread Performance Checker diagnostic (enabled in the scheme) catches main-thread I/O, lock contention, and semaphore waits. MetricKit delivers hang duration histograms from real users in the field. The 16ms rule is the standard answer to 'how long can work take on the main thread?'",
                "code": """// MetricKit — receive hang reports from field users (iOS 13+)
import MetricKit

class AppDelegate: UIResponder, UIApplicationDelegate, MXMetricManagerSubscriber {
    func application(_ app: UIApplication,
                     didFinishLaunchingWithOptions opts: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        MXMetricManager.shared.add(self)
        return true
    }

    func didReceive(_ payloads: [MXMetricPayload]) {
        for payload in payloads {
            if let hangMetrics = payload.applicationResponsivenessMetrics {
                // hangDuration histogram — p50, p90, p99 hang durations from real users
                print(hangMetrics.histogrammedApplicationHangTime)
            }
        }
    }
}""",
                "tip": "MetricKit is a differentiating answer at the staff level — it shows you think about production monitoring, not just local profiling. The 16ms threshold comes from 1000ms/60fps ≈ 16.67ms. On ProMotion displays (120fps), the threshold is 8ms. A common follow-up: 'What's the difference between a hang and an ANR?' On iOS, the system watchdog terminates apps stuck on the main thread for ~1-2 seconds (the 'Application Not Responding' threshold)."
            },
            {
                "title": "SwiftUI render performance: Self._printChanges(), .equatable(), and lazy containers",
                "body": "SwiftUI re-renders views when observed state changes. Self._printChanges() logs exactly which property triggered a body call — invaluable for diagnosing unnecessary renders. .equatable() wraps a view in EquatableView, skipping re-render if the view's inputs are equal. Lazy containers (LazyVStack, LazyHGrid) defer cell creation until they scroll into view.",
                "code": """struct ArticleRow: View, Equatable {
    let article: Article

    // SwiftUI will not call body if article == previous article
    static func == (lhs: ArticleRow, rhs: ArticleRow) -> Bool {
        lhs.article.id == rhs.article.id &&
        lhs.article.updatedAt == rhs.article.updatedAt
    }

    var body: some View {
        let _ = Self._printChanges()  // Debug only — remove before shipping
        VStack(alignment: .leading) {
            Text(article.title).font(.headline)
            Text(article.subtitle).font(.caption).foregroundStyle(.secondary)
        }
    }
}

// Use lazy container for long lists
ScrollView {
    LazyVStack(spacing: 12) {
        ForEach(articles) { article in
            ArticleRow(article: article).equatable()
        }
    }
}""",
                "tip": "Self._printChanges() is a production-quality debugging tool that interviewers appreciate seeing mentioned — it shows hands-on SwiftUI experience. The _equatable() modifier only helps when the view's Equatable conformance is cheaper than re-running body. If body is fast (just Text/Image composition), the conformance overhead may not be worth it. Know when to reach for it."
            },
            {
                "title": "Memory pressure: NSCache vs Dictionary, and image downsampling",
                "body": "NSCache is preferred over Dictionary for in-memory caches because the system can automatically evict entries under memory pressure. Dictionary holds strong references forever. Image downsampling — rendering a large image to a smaller CGImage before creating a UIImage — is the single most impactful change for reducing memory in image-heavy apps; loading a 4000x3000 image thumbnail with UIImage(named:) allocates the full resolution in memory.",
                "code": """// NSCache — auto-evicts under memory pressure, thread-safe
let imageCache = NSCache<NSURL, UIImage>()
imageCache.countLimit = 200
imageCache.totalCostLimit = 50 * 1024 * 1024   // 50 MB

// Downsample before storing in cache
func downsample(imageAt url: URL, to pointSize: CGSize, scale: CGFloat) -> UIImage? {
    let options: [CFString: Any] = [
        kCGImageSourceShouldCacheImmediately: false,
        kCGImageSourceShouldCache: false
    ]
    guard let source = CGImageSourceCreateWithURL(url as CFURL, options as CFDictionary) else { return nil }

    let maxDimension = max(pointSize.width, pointSize.height) * scale
    let thumbnailOptions: [CFString: Any] = [
        kCGImageSourceThumbnailMaxPixelSize: maxDimension,
        kCGImageSourceCreateThumbnailFromImageAlways: true,
        kCGImageSourceCreateThumbnailWithTransform: true,
        kCGImageSourceShouldCacheImmediately: true
    ]
    guard let cgImage = CGImageSourceCreateThumbnailAtIndex(source, 0, thumbnailOptions as CFDictionary) else { return nil }
    return UIImage(cgImage: cgImage)
}""",
                "tip": "Downsampling is the highest-impact single change for photo-heavy apps and almost always appears in performance interviews. The key distinction: UIImage(data:) and UIImage(named:) decode the full image into memory regardless of display size. CGImageSource thumbnailing creates a smaller CGImage at the pixel level. The memory difference for a gallery of 100 high-res photos can be 10x."
            },
        ],
        "try_it": [
            "Profile your app's main scroll view with Time Profiler. Apply Invert Call Tree + Hide System Libraries. Find the top 3 functions in your own code and assess whether they are doing unnecessary work on each frame.",
            "Use the Allocations instrument with heapshots to profile a push/pop navigation cycle. Take a heapshot before and after. If any of your view controllers or ViewModels appear in the generation diff, there is a cycle or over-retention to investigate.",
            "Add Self._printChanges() to a list row view. Scroll rapidly and observe the console. If unrelated properties are triggering re-renders, refactor to isolate state or add an Equatable conformance.",
            "Replace the largest UIImage usage in your app with the CGImageSource downsampling technique. Use Instruments Allocations to measure the memory reduction before and after. Document the result."
        ]
    },
    11: {
        "overview": "Testing and CI are the infrastructure that lets a team move fast without breaking things. Senior interviews test whether you write tests as first-class code, not as an afterthought. Staff interviews go further: can you design a CI pipeline that gives fast signal without being slow or flaky?",
        "concepts": [
            {
                "title": "XCTest unit tests: Given-When-Then, FIRST properties, and protocol mock injection",
                "body": "Good unit tests follow Given-When-Then structure (set up state, exercise the unit, assert the outcome) and the FIRST properties: Fast, Isolated, Repeatable, Self-validating, Timely. Mock injection via protocol substitution keeps tests isolated from external services. Tests that hit the network, filesystem, or clock are fragile and slow.",
                "code": """// Swift Testing style (preferred for new code)
import Testing
@testable import MyApp

@MainActor
struct ArticleViewModelTests {
    @Test("loadArticles populates articles on success")
    func loadArticles_withValidResponse_populatesArticles() async throws {
        // Given
        let mockRepo = MockArticleRepository(stubbedArticles: [.fixture()])
        let sut = ArticleListViewModel(repository: mockRepo)

        // When
        await sut.loadArticles()

        // Then
        #expect(sut.articles.count == 1)
        #expect(sut.isLoading == false)
        #expect(sut.errorMessage == nil)
    }

    @Test("loadArticles sets errorMessage on failure")
    func loadArticles_withNetworkError_setsErrorMessage() async throws {
        let mockRepo = MockArticleRepository(error: URLError(.notConnectedToInternet))
        let sut = ArticleListViewModel(repository: mockRepo)
        await sut.loadArticles()
        #expect(sut.errorMessage != nil)
    }
}""",
                "tip": "FIRST is a common interview prompt: 'What makes a good unit test?' If you list all five with explanations you stand out. The most violated property in iOS codebases is Isolated — tests that share global state (UserDefaults, singletons, file system) create order-dependent failures that are nightmare to debug. The fix is always dependency injection."
            },
            {
                "title": "Async testing: async test methods and XCTestExpectation for callbacks",
                "body": "Swift Testing and XCTest both support async test methods natively — mark the function async throws and use await directly. This is far superior to XCTestExpectation for async/await code because expectations require manually balancing fulfill() calls and can obscure the actual failure. Use XCTestExpectation only for callback-based APIs that cannot be awaited.",
                "code": """// Modern: async test method — no expectation needed
import XCTest
@testable import MyApp

final class SearchServiceTests: XCTestCase {
    func test_search_returnsMatchingResults() async throws {
        let sut = SearchService(client: MockHTTPClient(fixture: .searchResults))
        let results = try await sut.search(query: "swift")
        XCTAssertFalse(results.isEmpty)
        XCTAssertTrue(results.allSatisfy { $0.title.localizedCaseInsensitiveContains("swift") })
    }
}

// Legacy: XCTestExpectation for callback-based APIs only
func test_legacyCallback_returnsData() {
    let exp = expectation(description: "callback fires")
    legacyService.fetch { result in
        XCTAssertNotNil(try? result.get())
        exp.fulfill()
    }
    wait(for: [exp], timeout: 2.0)
}""",
                "tip": "Candidates who reach for XCTestExpectation for async/await code have not kept up with modern testing. The interviewer probe is: 'How do you test an async function?' The correct answer is 'async test method with await.' Only fall back to XCTestExpectation when the API under test uses callbacks and cannot be bridged to async/await cleanly."
            },
            {
                "title": "XCUITest: accessibility identifiers as stable hooks and element waits",
                "body": "XCUITest drives the app through the Accessibility layer. Accessibility identifiers are the most stable way to address elements — unlike labels (which change with localization) or hierarchy positions (which change with layout). Never use sleep() to wait for elements; use XCUIElement.waitForExistence(timeout:) which polls efficiently and fails fast.",
                "code": """// Production code — set identifier once in the view
struct LoginView: View {
    @State private var email = ""
    @State private var password = ""

    var body: some View {
        VStack {
            TextField("Email", text: $email)
                .accessibilityIdentifier("loginEmailField")
            SecureField("Password", text: $password)
                .accessibilityIdentifier("loginPasswordField")
            Button("Sign In") { signIn() }
                .accessibilityIdentifier("loginSignInButton")
        }
    }
}

// XCUITest
final class LoginUITests: XCTestCase {
    func test_login_withValidCredentials_navigatesToHome() {
        let app = XCUIApplication()
        app.launch()

        let emailField = app.textFields["loginEmailField"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 3))  // not sleep(3)
        emailField.tap()
        emailField.typeText("user@example.com")

        app.secureTextFields["loginPasswordField"].tap()
        app.secureTextFields["loginPasswordField"].typeText("password123")

        app.buttons["loginSignInButton"].tap()
        XCTAssertTrue(app.navigationBars["Home"].waitForExistence(timeout: 5))
    }
}""",
                "tip": "waitForExistence(timeout:) vs sleep is the most common XCUITest interview question. sleep is flaky (too short on slow CI machines, too long always) and wastes wall clock time. waitForExistence polls at the element level and returns the moment it appears, making tests both faster and more reliable. Always use waits, never sleeps."
            },
            {
                "title": "Snapshot testing: component-level snapshots and CI integration",
                "body": "Snapshot tests render a view and compare the output to a stored reference image. They catch unintended visual regressions that unit tests miss. The best practice is to snapshot at the component level (individual card, button, cell) rather than full screens — smaller snapshots are less fragile to layout changes elsewhere. The reference images must be committed to source control and updated when design changes intentionally.",
                "code": """// Using swift-snapshot-testing (pointfreeco/swift-snapshot-testing)
import SnapshotTesting
import SwiftUI
import XCTest

final class ArticleCardSnapshotTests: XCTestCase {
    func test_articleCard_default() {
        let view = ArticleCard(article: .fixture())
            .frame(width: 375)   // iPhone SE width
        assertSnapshot(of: view, as: .image(layout: .sizeThatFits))
    }

    func test_articleCard_bookmarked() {
        let view = ArticleCard(article: .fixture(isBookmarked: true))
            .frame(width: 375)
        assertSnapshot(of: view, as: .image(layout: .sizeThatFits))
    }

    func test_articleCard_longTitle() {
        let long = Article.fixture(title: String(repeating: "Very Long Title ", count: 5))
        let view = ArticleCard(article: long).frame(width: 375)
        assertSnapshot(of: view, as: .image(layout: .sizeThatFits))
    }
}""",
                "tip": "The interview question on snapshot tests: 'When do you update the snapshots?' Answer: only when the design intentionally changed. The workflow is: PR fails CI → designer confirms the change is intentional → developer runs the update command (record: true) → new images committed → CI passes. Accidental snapshot updates committed to main are how regressions get silently accepted."
            },
            {
                "title": "CI pipeline design: fast unit tests, slower UI tests, and parallelization",
                "body": "A well-designed iOS CI pipeline runs the fastest signal first: unit tests on every commit (target <2 minutes), UI tests on every PR (target <15 minutes), nightly full regression. Parallel test execution (xcodebuild -parallel-testing-enabled YES) and test plan splitting across multiple simulators drastically reduce wall clock time for large test suites.",
                "code": """# .github/workflows/ci.yml (illustrative)
# Unit tests — every commit, must be <2 min
- name: Unit Tests
  run: |
    xcodebuild test \\
      -scheme MyAppUnitTests \\
      -destination 'platform=iOS Simulator,name=iPhone 16' \\
      -parallel-testing-enabled YES \\
      -maximum-parallel-testing-workers 4 \\
      | xcpretty

# UI tests — every PR, target <15 min
- name: UI Tests
  run: |
    xcodebuild test \\
      -scheme MyAppUITests \\
      -destination 'platform=iOS Simulator,name=iPhone 16' \\
      -testPlan CriticalFlows \\
      | xcpretty

# Nightly: full suite including slow integration tests
# Triggered by cron, runs on larger CI machines""",
                "tip": "Staff candidates are expected to have opinions about CI design. The key insight: UI tests are 10-100x slower than unit tests, so gate the most expensive tests on PRs, not commits. Flaky UI tests are worse than no tests — they train engineers to ignore failures. The solution is quarantine: move flaky tests to a separate scheme, fix them, then re-promote. Never delete a test; understand why it is flaky."
            },
        ],
        "try_it": [
            "Pick the most complex ViewModel in your project and write Given-When-Then unit tests for its three most important state transitions. Inject dependencies via protocol mocks. Run them isolated from the network with no real network calls.",
            "Convert one test that uses XCTestExpectation for an async/await-based operation to use an async test method instead. Compare the readability and measure the execution time difference.",
            "Add accessibility identifiers to a login or onboarding flow. Write one XCUITest that covers the happy path end-to-end. Run it in CI (even GitHub Actions free tier) and observe the wall clock time.",
            "Add swift-snapshot-testing to your project. Create snapshots for three states of one component (default, loading, error). Intentionally change the component's appearance and observe the CI failure diff."
        ]
    },
    12: {
        "overview": "Mobile system design is the staff-level interview format where you design an entire feature or app subsystem in 45-60 minutes. Interviewers are testing breadth and depth simultaneously: can you design an offline-first feed, reason about pagination strategies, represent state as a state machine, and modularize for a 100-engineer team? This week synthesizes all prior topics.",
        "concepts": [
            {
                "title": "Offline-first: source of truth, optimistic updates, and conflict resolution",
                "body": "Offline-first means the local database is the source of truth for the UI, and the network is a sync mechanism. The UI reads from and writes to the local store immediately (optimistic update), then the background sync reconciles with the server. Conflict resolution policy must be explicit: last-write-wins, server-wins, or merge — and must be documented for each entity type.",
                "code": """// Offline-first write flow
@MainActor
final class BookmarkViewModel {
    func bookmark(article: Article) async {
        // 1. Optimistic local write — UI updates immediately
        await localStore.setBookmarked(true, articleId: article.id)

        // 2. Background sync — failure doesn't undo the UI update
        do {
            try await apiClient.bookmark(articleId: article.id)
        } catch {
            // Log for retry queue; do not revert unless conflict policy requires it
            await retryQueue.enqueue(.bookmark(article.id))
        }
    }

    func resolveConflict(local: Article, remote: Article) -> Article {
        // Server-wins for bookmark state (server is authoritative)
        var resolved = local
        resolved.isBookmarked = remote.isBookmarked
        return resolved
    }
}""",
                "tip": "The system design question 'design a Twitter-like feed with offline support' is extremely common at staff level. The expected answer structure: (1) local DB as source of truth, (2) optimistic writes, (3) explicit conflict resolution policy. Weak candidates say 'check connectivity and show an error.' Strong candidates immediately reach for a local-first model with a sync layer."
            },
            {
                "title": "Pagination: cursor vs offset — why cursor wins at scale",
                "body": "Offset pagination (page=2&per_page=20) breaks when items are inserted or deleted between page requests — the user sees duplicates or skips items. Cursor pagination uses an opaque server-provided token pointing to the last item seen, guaranteeing a stable window regardless of insertions. At scale, cursor pagination is also more efficient since the database does not need to scan and discard N offset rows.",
                "code": """struct PaginatedFeed {
    var items: [Article] = []
    var nextCursor: String?   // nil means no more pages
    var isLoading = false

    mutating func append(page: FeedPage) {
        items.append(contentsOf: page.articles)
        nextCursor = page.nextCursor
    }
}

// Load next page using cursor
func loadNextPage() async {
    guard let cursor = feed.nextCursor, !feed.isLoading else { return }
    feed.isLoading = true
    defer { feed.isLoading = false }
    let page = try? await api.fetchFeed(after: cursor)
    if let page { feed.append(page: page) }
}

// Trigger load when near the end of the visible list
.onAppear {
    if article == feed.items.last {
        Task { await loadNextPage() }
    }
}""",
                "tip": "Cursor vs offset is a classic interview question. The exact failure mode to describe: 'If 5 new posts are inserted at the top while the user reads page 1, page 2 starts 5 items too early, so the user sees those 5 posts again.' Cursor avoids this entirely. The follow-up: 'What is the cursor made of?' Server-defined — often a base64-encoded timestamp or ID. The client treats it as opaque."
            },
            {
                "title": "State machine design: enum-based states and impossible states",
                "body": "Modeling screen state as an enum makes illegal state combinations impossible to represent. Instead of three booleans (isLoading, hasError, isEmpty), use a single enum that can only ever be in one valid state at a time. This eliminates an entire class of bugs where isLoading and hasError are both true, which has no valid UI representation.",
                "code": """// BAD: three booleans — 8 combinations, most are invalid
struct BadState {
    var isLoading: Bool
    var hasError: Bool
    var items: [Article]
}

// GOOD: enum — exactly the valid states
enum FeedState: Equatable {
    case idle
    case loading
    case loaded([Article])
    case empty
    case failed(message: String)
}

struct FeedView: View {
    var state: FeedState

    var body: some View {
        switch state {
        case .idle:       Color.clear
        case .loading:    ProgressView()
        case .loaded(let items): ArticleList(items: items)
        case .empty:      EmptyStateView()
        case .failed(let msg): ErrorView(message: msg)
        }
    }
}""",
                "tip": "The phrase 'make impossible states unrepresentable' is the expected answer to 'how do you model complex screen state?' It's directly from the Swift/functional programming community and signals you have moved beyond ad-hoc boolean flags. Staff interviewers listen for this idiom because it indicates an engineer who designs systems that fail loudly at compile time rather than silently at runtime."
            },
            {
                "title": "Push notifications: APNs token refresh and notification service extensions",
                "body": "The APNs device token must be refreshed on every launch — it can change after a backup restore or OS reinstall, and using a stale token causes silent notification failure. Notification Service Extensions allow decrypting, enriching, or downloading media for notifications in a 30-second background window before delivery, even when the app is not running.",
                "code": """// AppDelegate — refresh token on every launch
func application(_ app: UIApplication,
                 didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
    // Convert binary token to hex string
    let token = deviceToken.map { String(format: "%02x", $0) }.joined()
    // Always upload, even if it looks the same — token can change silently
    Task { await notificationService.registerToken(token) }
}

// Notification Service Extension (separate target)
class NotificationServiceExtension: UNNotificationServiceExtension {
    override func didReceive(_ request: UNNotificationRequest,
                             withContentHandler handler: @escaping (UNNotificationContent) -> Void) {
        let content = request.content.mutableCopy() as! UNMutableNotificationContent
        // Download and attach media before notification is shown
        if let urlString = content.userInfo["media_url"] as? String,
           let url = URL(string: urlString) {
            downloadAttachment(url) { attachment in
                if let a = attachment { content.attachments = [a] }
                handler(content)   // must call within 30 seconds
            }
        } else { handler(content) }
    }
}""",
                "tip": "The APNs token refresh requirement is the most common production push notification bug. Engineers assume the token is stable and only register once. It is not. The correct pattern is: register on every launch, unconditionally upload the token to your server. Your server should handle idempotent upserts. The 30-second limit on Notification Service Extensions is also probed — what happens if you exceed it? The original notification is delivered without modification."
            },
            {
                "title": "Modular app at scale: team topology mirrors module topology, circular dependencies",
                "body": "At 50+ engineers, a module dependency graph directly affects team autonomy. When a team's module imports another team's module, any change by the other team can break yours — coupling in the code creates coupling in the org. Circular dependencies (A imports B, B imports A) always indicate a missing abstraction in a shared layer. The compiler rejects circular module dependencies, making them a build-time error, not a runtime surprise.",
                "code": """// Circular dependency — symptom of missing abstraction
// AuthFeature imports ProfileFeature (to show profile after login)
// ProfileFeature imports AuthFeature (to check auth state)
// → Circular — will not compile

// Fix: extract the shared abstraction to Domain layer
// Domain/Sources/UserSessionProtocol.swift
public protocol UserSessionProtocol: Sendable {
    var currentUser: User? { get }
    func logout() async
}

// AuthFeature depends on Domain.UserSessionProtocol (not ProfileFeature)
// ProfileFeature depends on Domain.UserSessionProtocol (not AuthFeature)
// Both feature modules are now independent; Domain is the shared abstraction

// Conway's Law consequence:
// If AuthTeam and ProfileTeam cannot change independently, they are coupled.
// The solution is always a new abstraction in the shared Domain layer.""",
                "tip": "The circular dependency question at staff level is a design smell detector. When an interviewer shows you a dependency graph with a cycle and asks 'how do you fix this?', the answer is never 'just use weak imports or workarounds.' The answer is 'extract the shared concept to a lower-level module that both can depend on.' This is Conway's Law applied to Swift modules: if two teams cannot work independently, find the missing shared abstraction."
            },
        ],
        "try_it": [
            "Design on paper (or a whiteboard tool) a complete offline-first bookmarking feature: local database schema, sync service protocol, conflict resolution policy, and the ViewModel state machine. Identify every state the UI can be in and verify no two booleans are needed.",
            "Replace a boolean-flag-based loading/error/empty state in your app with a single enum-based state. Walk through every switch case and verify the UI handles each state explicitly with no 'else' fallback that could hide a missing state.",
            "Audit your app's push notification registration code. Is the token uploaded on every launch unconditionally? If not, fix it. Check that your server endpoint is idempotent (handles duplicate registrations gracefully).",
            "Draw the module dependency graph of your app (even if it is a monolith, pretend each major folder is a module). Find the longest dependency chain. Find any circular references. For each circular reference, name the missing abstraction that would break it."
        ]
    },
}
