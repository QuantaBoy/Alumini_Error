const BASE_URL = "http://localhost:5000/api";

export async function getPosts() {
  const response = await fetch(`${BASE_URL}/posts`);
  return response.json();
}
