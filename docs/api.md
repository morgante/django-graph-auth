API Endpoints
========

## Queries

### Get Users
```
query {
  users {
    edges {
      node {
        id,
        firstName
      }
    }
  }
}
```

### Get Current User
```
query {
  me {
    id,
    firstName,
    lastName,
    email
  }
}
```

## Mutations

### Registration
```
mutation {
  registerUser(input: {
    email: "morgante@mastermade.co",
    password: "test_password",
    firstName: "Morgante",
    lastName: "Pell"
  }) {
    ok,
    user {
      id,
      firstName,
      email,
      token
    }
  }
}
```

### Log In
Log in to get a JWT for future requests.
```
mutation {
  loginUser(input: {
    email: "morgante@mastermade.co",
    password: "test_password"
  }) {
    ok,
    user {
      id,
      firstName,
      email,
      token
    }
  }
}
```

### Reset Password
First send a password reset request with this mutation:
```
mutation {
  resetPasswordRequest(input: {
    email: "morgante@mastermade.co"
  }) {
    ok
  }
}
```

This will then send an email to the user including a link. This link includes an `id` and a `token`. You then make another query with those components and the new password:
```
mutation {
  resetPassword(input: {
    id: "uid",
    token: "token",
    password: "new_password"
  }) {
    ok,
    user {
      id
    }
  }
}
```


### Update User
Logged in users can update themselves.

Please note that the user needs to provide their current password to change their password.
Changing the password may reset a user's session.
```
mutation {
  updateUser(input: {
    email: "new@mastermade.co"
    firstName: "newFirst",
    lastName: "newLast",
    username: "newname"
    password: "excellent_password"
  }) {
    ok
    result {
      email
      firstName
      lastName
    }
  }
}
```
