import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";

export interface Repo {
  id: string;
  github_url: string;
  name: string;
  status: "pending" | "processing" | "ready" | "failed";
  created_at: string;
}

export function useRepos() {
  return useQuery<Repo[]>({
    queryKey: ["repos"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/repos");
      return data;
    },
  });
}

export function useCreateRepo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (github_url: string) => {
      const { data } = await api.post("/api/v1/repos", { github_url });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repos"] });
    },
  });
}
