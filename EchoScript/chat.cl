// plic langjam entry: "chatlang"
// A tiny event-driven language whose only job is running a chat room.

var join_count = 0
var banned_words = ["spam", "scam"]

func format_message(username, text) {
    return "[" + now() + "] " + username + ": " + text
}

func contains(list_value, item) {
    var i = 0
    while (i < len(list_value)) {
        if (list_value[i] == item) {
            return true
        }
        i = i + 1
    }
    return false
}

func is_blocked(text) {
    var words = split(lower(text), " ")
    var i = 0
    while (i < len(words)) {
        if (contains(banned_words, words[i])) {
            return true
        }
        i = i + 1
    }
    return false
}

on connect(id, username) {
    join_count = join_count + 1
    broadcast("* " + username + " joined the chat (" + str(join_count) + " joins so far)")
    send(id, "Welcome, " + username + "! Commands: /history, /users, /quit")
}

on message(id, username, text) {
    if (text == "/history") {
        var recent = history(10)
        if (len(recent) == 0) {
            send(id, "(no messages yet)")
        } else {
            var i = 0
            while (i < len(recent)) {
                send(id, recent[i])
                i = i + 1
            }
        }
    } else {
        if (text == "/users") {
            send(id, "Online: " + join(users(), ", "))
        } else {
            if (is_blocked(text)) {
                send(id, "* message blocked (banned word)")
            } else {
                broadcast(format_message(username, text))
            }
        }
    }
}

on disconnect(id, username) {
    broadcast("* " + username + " left the chat")
}
